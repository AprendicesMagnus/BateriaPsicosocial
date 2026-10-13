import logging
import secrets
from datetime import datetime, timedelta
from random import randint
from uuid import UUID

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.crypto import email_valido, hash_password, password_valida, utcnow, verificar_password
from app.core.errors import AppError
from app.core.security import crear_token_reset, crear_token_sesion, decodificar_token
from app.models.user import CodigoVerificacion, Rol, Usuario
from app.services.correo import enviar_codigo_verificacion
from app.services.perfil import proxima_edicion

settings = get_settings()
logger = logging.getLogger(__name__)

# Client ID público de Google Cloud (no es secreto, puede vivir en el código).
GOOGLE_CLIENT_ID = "615740449491-340ojlb2h90f13j4ut7u0rhtm2k90589.apps.googleusercontent.com"


# Roles que una persona puede elegir al registrarse (tradicional o con Google).
# SUPER_ADMINISTRADOR nunca se puede asignar desde el registro.
ROLES_AUTOREGISTRO = {"JEFE", "ADMINISTRADOR", "EVALUADOR_SST"}


def usuario_publico(usuario: Usuario) -> dict:
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "rol": usuario.rol.codigo,
        "emailVerificado": usuario.email_verificado,
        "estado": usuario.estado,
        "organizacionId": str(usuario.organizacion_id) if usuario.organizacion_id else None,
        # Nombre de la empresa activa: lo muestra el título de Reportes
        "organizacionNombre": usuario.organizacion.nombre if usuario.organizacion else None,
        "areaId": str(usuario.area_id) if usuario.area_id else None,
        "numeroIdentificacion": usuario.numero_identificacion,
        "cargo": usuario.cargo,
        # El frontend lo usa para no dejar entrar a los pacientes del enlace a las páginas internas
        "esInvitado": usuario.es_invitado,
        "fotoUrl": usuario.foto_url,
        "perfilActualizadoEn": usuario.perfil_actualizado_en.isoformat() if usuario.perfil_actualizado_en else None,
        "proximaEdicionPerfil": (
            proxima_edicion(usuario).isoformat() if proxima_edicion(usuario) else None
        ),
    }


def _obtener_rol(db: Session, codigo: str) -> Rol:
    rol = db.query(Rol).filter(Rol.codigo == codigo).first()
    if rol is None:
        raise AppError(500, "El catálogo de roles no está inicializado.")
    return rol


def _generar_codigo() -> str:
    return str(randint(100000, 999999))


def crear_y_enviar_codigo(db: Session, usuario: Usuario, tipo: str) -> None:
    codigo = _generar_codigo()
    registro = CodigoVerificacion(
        usuario_id=usuario.id,
        codigo=codigo,
        tipo=tipo,
        expira_en=utcnow() + timedelta(minutes=settings.codigo_expira_minutos),
    )
    db.add(registro)
    db.commit()
    enviar_codigo_verificacion(usuario.email, usuario.nombre, codigo, tipo)


def registrar(db: Session, data) -> dict:
    if not data.nombre or not data.apellido or not data.email or not data.password:
        raise AppError(400, "Todos los campos son obligatorios.")
    if not email_valido(str(data.email)):
        raise AppError(400, "El formato del correo electrónico no es válido.")
    if not password_valida(data.password):
        raise AppError(
            400,
            "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números.",
        )
    if data.rol not in ROLES_AUTOREGISTRO:
        raise AppError(400, "El rol seleccionado no es válido.")
    if db.query(Usuario).filter(Usuario.email == str(data.email).lower()).first():
        raise AppError(409, "Ya existe una cuenta registrada con este correo.")

    usuario = Usuario(
        nombre=data.nombre.strip(),
        apellido=data.apellido.strip(),
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        rol_id=_obtener_rol(db, data.rol).id,
        email_verificado=False,
        estado="ACTIVO",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario.id).one()
    crear_y_enviar_codigo(db, usuario, "VERIFICACION_EMAIL")
    return {
        "message": "Cuenta creada. Revisa tu correo para verificar tu cuenta.",
        "email": usuario.email,
    }


def verificar_email(db: Session, email: str, codigo: str) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == email.lower()).first()
    if usuario is None:
        raise AppError(404, "No existe una cuenta con este correo.")
    if usuario.email_verificado:
        return {"message": "La cuenta ya estaba verificada."}

    registro = (
        db.query(CodigoVerificacion)
        .filter(
            CodigoVerificacion.usuario_id == usuario.id,
            CodigoVerificacion.tipo == "VERIFICACION_EMAIL",
            CodigoVerificacion.codigo == codigo,
            CodigoVerificacion.usado.is_(False),
            CodigoVerificacion.expira_en > utcnow(),
        )
        .order_by(CodigoVerificacion.creado_en.desc())
        .first()
    )
    if registro is None:
        raise AppError(400, "El código es inválido o ha expirado.")

    usuario.email_verificado = True
    registro.usado = True
    db.commit()
    return {"message": "Cuenta verificada correctamente."}


def reenviar_codigo(db: Session, email: str, tipo: str) -> dict:
    if tipo not in {"VERIFICACION_EMAIL", "RESET_PASSWORD"}:
        raise AppError(400, "Solicitud inválida.")
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.email == email.lower()).first()
    if usuario is None:
        return {"message": "Si el correo existe, se ha enviado un nuevo código."}
    if tipo == "VERIFICACION_EMAIL" and usuario.email_verificado:
        return {"message": "La cuenta ya estaba verificada."}
    crear_y_enviar_codigo(db, usuario, tipo)
    return {"message": "Se ha enviado un nuevo código."}


def login(db: Session, email: str, password: str) -> dict:
    if not email or not password:
        raise AppError(400, "Correo y contraseña son obligatorios.")
    usuario = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.email == email.lower())
        .first()
    )
    # Los pacientes del enlace no inician sesión con correo y contraseña
    if usuario is None or usuario.es_invitado:
        raise AppError(401, "Credenciales incorrectas.")

    ahora = utcnow()
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        minutos = int((usuario.bloqueado_hasta - ahora).total_seconds() // 60) + 1
        raise AppError(
            423,
            f"Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta de nuevo en {minutos} minuto(s).",
        )
    if usuario.estado != "ACTIVO":
        raise AppError(403, "Esta cuenta se encuentra inactiva.")

    if not verificar_password(password, usuario.password_hash):
        intentos = usuario.intentos_fallidos + 1
        bloqueado = intentos >= settings.max_intentos_login
        usuario.intentos_fallidos = 0 if bloqueado else intentos
        usuario.bloqueado_hasta = ahora + timedelta(minutes=settings.bloqueo_minutos) if bloqueado else None
        db.commit()
        if bloqueado:
            raise AppError(
                423,
                f"Cuenta bloqueada temporalmente por {settings.bloqueo_minutos} minutos tras 5 intentos fallidos.",
            )
        raise AppError(401, "Credenciales incorrectas.")

    if not usuario.email_verificado:
        raise AppError(
            403,
            "Debes verificar tu correo antes de iniciar sesión.",
            requiresVerification=True,
            email=usuario.email,
        )

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.commit()
    token = crear_token_sesion(str(usuario.id), usuario.rol.codigo, usuario.email)
    return {"token": token, "usuario": usuario_publico(usuario)}


def login_con_google(db: Session, credential: str, rol: str | None = None) -> dict:
    # Verifica con los servidores de Google que el token es real y no fue
    # falsificado, y que efectivamente fue emitido para nuestro Client ID.
    try:
        # clock_skew_in_seconds tolera pequeños desfases del reloj del equipo, causa común
        # de "Token used too early" cuando la hora de Windows no está sincronizada.
        payload = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=30
        )
    except ValueError as exc:
        # El motivo real (audiencia incorrecta, token vencido, reloj, firma...) queda en el
        # log del servidor para diagnosticar; al cliente solo se le da un mensaje genérico.
        logger.warning("Google rechazó el token: %s", exc)
        raise AppError(401, "No se pudo validar tu cuenta de Google. Intenta de nuevo.")

    email = payload.get("email")
    if not email or not payload.get("email_verified", False):
        raise AppError(401, "No se pudo verificar el correo de la cuenta de Google.")

    nombre = (payload.get("given_name") or payload.get("name") or "Usuario").strip()
    apellido = (payload.get("family_name") or "Google").strip()

    usuario = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.email == email.lower())
        .first()
    )

    if usuario is None:
        # Primera vez que esta persona entra. Antes de crear la cuenta se le pide
        # que elija su rol (pantalla rápida en el frontend). Mientras no lo envíe,
        # NO se crea nada y se responde requiereRol=True.
        if rol is None:
            return {
                "requiereRol": True,
                "email": email.lower(),
                "nombre": nombre,
                "apellido": apellido,
            }
        if rol not in ROLES_AUTOREGISTRO:
            raise AppError(400, "El rol seleccionado no es válido.")

        # Se le pone una contraseña aleatoria e inutilizable porque nunca la
        # va a necesitar (siempre entrará por Google).
        usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=email.lower(),
            password_hash=hash_password(secrets.token_urlsafe(32)),
            rol_id=_obtener_rol(db, rol).id,
            email_verificado=True,
            estado="ACTIVO",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        usuario = (
            db.query(Usuario)
            .options(joinedload(Usuario.rol))
            .filter(Usuario.id == usuario.id)
            .one()
        )
    else:
        if usuario.estado != "ACTIVO":
            raise AppError(403, "Esta cuenta se encuentra inactiva.")
        if not usuario.email_verificado:
            usuario.email_verificado = True
            db.commit()

    token = crear_token_sesion(str(usuario.id), usuario.rol.codigo, usuario.email)
    return {"token": token, "usuario": usuario_publico(usuario)}


def forgot_password(db: Session, email: str) -> dict:
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.email == email.lower()).first()
    if usuario:
        crear_y_enviar_codigo(db, usuario, "RESET_PASSWORD")
    return {
        "message": "Si el correo está registrado, recibirás un código para restablecer tu contraseña."
    }


def verify_reset_code(db: Session, email: str, codigo: str) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == email.lower()).first()
    if usuario is None:
        raise AppError(400, "El código es inválido o ha expirado.")
    registro = (
        db.query(CodigoVerificacion)
        .filter(
            CodigoVerificacion.usuario_id == usuario.id,
            CodigoVerificacion.tipo == "RESET_PASSWORD",
            CodigoVerificacion.codigo == codigo,
            CodigoVerificacion.usado.is_(False),
            CodigoVerificacion.expira_en > utcnow(),
        )
        .order_by(CodigoVerificacion.creado_en.desc())
        .first()
    )
    if registro is None:
        raise AppError(400, "El código es inválido o ha expirado.")
    registro.usado = True
    db.commit()
    return {"resetToken": crear_token_reset(str(usuario.id))}


def reset_password(db: Session, reset_token: str, password: str) -> dict:
    if not reset_token or not password:
        raise AppError(400, "Solicitud inválida.")
    if not password_valida(password):
        raise AppError(
            400,
            "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números.",
        )
    payload = decodificar_token(reset_token, error_sesion=False)
    if payload.get("purpose") != "reset_password":
        raise AppError(400, "Token inválido.")
    usuario = db.query(Usuario).filter(Usuario.id == payload.get("sub")).first()
    if usuario is None:
        raise AppError(400, "Token inválido.")
    usuario.password_hash = hash_password(password)
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.commit()
    return {"message": "Contraseña restablecida correctamente."}


def me(usuario: Usuario) -> dict:
    return {"usuario": usuario_publico(usuario)}