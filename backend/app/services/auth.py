import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from random import randint
from uuid import UUID

from fastapi import Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.crypto import email_valido, hash_password, password_valida, utcnow, verificar_password
from app.core.errors import AppError
from app.core.security import crear_token, crear_token_reset, decodificar_token
from app.models.security import CodigoDosPasos
from app.models.user import CodigoVerificacion, Rol, Usuario
from app.services import auditoria as auditoria_service
from app.services.correo import enviar_codigo_2fa, enviar_codigo_verificacion
from app.services import sesiones as sesiones_service
from app.services.perfil import proxima_edicion, resolucion_bloqueada_hasta

settings = get_settings()
logger = logging.getLogger(__name__)

# Client ID público de Google Cloud (no es secreto, puede vivir en el código).
GOOGLE_CLIENT_ID = "615740449491-340ojlb2h90f13j4ut7u0rhtm2k90589.apps.googleusercontent.com"


# Roles que una persona puede elegir al registrarse (tradicional o con Google).
# SUPER_ADMINISTRADOR nunca se puede asignar desde el registro.
ROLES_AUTOREGISTRO = {"JEFE", "ADMINISTRADOR", "EVALUADOR_SST"}

# Version de la politica de tratamiento de datos que se acepta al crear la cuenta.
# Debe coincidir con POLITICA_DATOS.version de frontend/src/utils/responsableDatos.js.
POLITICA_DATOS_VERSION = "1.0"


def _exigir_aceptacion_politica(acepta: bool) -> None:
    """Quien crea una cuenta debe aceptar la politica de tratamiento de datos."""
    if acepta is not True:
        raise AppError(400, "Debes aceptar la política de tratamiento de datos para crear tu cuenta.")


def _exigir_resolucion_psicologo(rol: str, numero: str | None) -> str | None:
    """El Psicologo debe registrar su número de resolución (6 dígitos); los demás roles no."""
    if rol == "EVALUADOR_SST":
        if not numero or not numero.isdigit() or len(numero) != 6:
            raise AppError(400, "El número de resolución es obligatorio y debe tener exactamente 6 dígitos.")
        return numero
    return None


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
        "numeroResolucion": usuario.numero_resolucion,
        "resolucionVerificada": usuario.resolucion_verificada,
        "resolucionIntentos": usuario.resolucion_intentos,
        "resolucionBloqueadaHasta": (
            resolucion_bloqueada_hasta(usuario).isoformat()
            if resolucion_bloqueada_hasta(usuario)
            else None
        ),
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


def registrar(db: Session, data, request: Request | None = None) -> dict:
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
    numero_resolucion = _exigir_resolucion_psicologo(data.rol, getattr(data, "numeroResolucion", None))
    _exigir_aceptacion_politica(getattr(data, "aceptaPolitica", False))
    if db.query(Usuario).filter(Usuario.email == str(data.email).lower()).first():
        raise AppError(409, "Ya existe una cuenta registrada con este correo.")

    usuario = Usuario(
        nombre=data.nombre.strip(),
        apellido=data.apellido.strip(),
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        rol_id=_obtener_rol(db, data.rol).id,
        numero_resolucion=numero_resolucion,
        email_verificado=False,
        politica_version=POLITICA_DATOS_VERSION,
        politica_aceptada_en=utcnow(),
        estado="ACTIVO",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario.id).one()
    auditoria_service.registrar_auditoria(
        db,
        usuario=usuario,
        accion="POLITICA_ACEPTADA",
        entidad="Usuario",
        entidad_id=str(usuario.id),
        request=request,
        nota=f"Versión {POLITICA_DATOS_VERSION}",
    )
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


ROLES_REQUIEREN_2FA = {"SUPER_ADMINISTRADOR", "ADMINISTRADOR", "JEFE", "EVALUADOR_SST"}
DOS_PASOS_EXPIRA_MINUTOS = 5
DOS_PASOS_MAX_INTENTOS = 5


def _hash_codigo_2fa(codigo: str) -> str:
    return hmac.new(settings.jwt_secret.encode("utf-8"), codigo.encode("utf-8"), hashlib.sha256).hexdigest()


def _emitir_codigo_2fa(db: Session, usuario: Usuario) -> str:
    reciente = db.query(CodigoDosPasos).filter(
        CodigoDosPasos.usuario_id == usuario.id,
        CodigoDosPasos.usado.is_(False),
        CodigoDosPasos.expira_en > utcnow(),
        CodigoDosPasos.creado_en > utcnow() - timedelta(seconds=30),
    ).first()
    if reciente:
        return ""  # Ya existe un código vigente; no reenviar para evitar spam.
    db.query(CodigoDosPasos).filter(
        CodigoDosPasos.usuario_id == usuario.id,
        CodigoDosPasos.usado.is_(False),
    ).update({"usado": True}, synchronize_session=False)
    codigo = f"{secrets.randbelow(900000) + 100000:06d}"
    registro = CodigoDosPasos(
        usuario_id=usuario.id,
        codigo_hash=_hash_codigo_2fa(codigo),
        expira_en=utcnow() + timedelta(minutes=DOS_PASOS_EXPIRA_MINUTOS),
        intentos=0,
        usado=False,
    )
    db.add(registro)
    db.commit()
    if not enviar_codigo_2fa(usuario.email, usuario.nombre, codigo):
        registro.usado = True
        db.commit()
        raise AppError(503, "No fue posible enviar el código de seguridad. Intenta nuevamente más tarde.")
    return codigo


def _preparar_acceso(db: Session, usuario: Usuario, request, trusted_device_token: str | None = None) -> dict:
    if usuario.rol.codigo in ROLES_REQUIEREN_2FA and not sesiones_service.dispositivo_es_confiable(db, usuario, trusted_device_token, request):
        _emitir_codigo_2fa(db, usuario)
        challenge = crear_token(
            {"sub": str(usuario.id), "purpose": "login_2fa"},
            DOS_PASOS_EXPIRA_MINUTOS,
        )
        return {
            "requiere2FA": True,
            "challengeToken": challenge,
            "email": usuario.email,
            "mensaje": "Enviamos un código de seguridad a tu correo electrónico.",
        }

    resultado = sesiones_service.crear_sesion(db, usuario, request)
    resultado["usuario"] = usuario_publico(usuario)
    db.commit()
    return resultado


def verificar_codigo_login(db: Session, challenge_token: str, codigo: str, request, confiar_dispositivo: bool = False) -> dict:
    payload = decodificar_token(challenge_token, error_sesion=False)
    if payload.get("purpose") != "login_2fa":
        raise AppError(400, "La solicitud de verificación no es válida.")
    usuario = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.id == payload.get("sub"), Usuario.estado == "ACTIVO")
        .first()
    )
    if usuario is None or usuario.rol.codigo not in ROLES_REQUIEREN_2FA:
        raise AppError(400, "La solicitud de verificación no es válida.")

    registro = (
        db.query(CodigoDosPasos)
        .filter(
            CodigoDosPasos.usuario_id == usuario.id,
            CodigoDosPasos.usado.is_(False),
            CodigoDosPasos.expira_en > utcnow(),
        )
        .order_by(CodigoDosPasos.creado_en.desc())
        .first()
    )
    if registro is None:
        raise AppError(400, "El código ha expirado. Solicita uno nuevo.")
    if registro.intentos >= DOS_PASOS_MAX_INTENTOS:
        registro.usado = True
        db.commit()
        raise AppError(429, "Superaste el número de intentos. Solicita un nuevo código.")
    if not secrets.compare_digest(registro.codigo_hash, _hash_codigo_2fa(codigo)):
        registro.intentos += 1
        if registro.intentos >= DOS_PASOS_MAX_INTENTOS:
            registro.usado = True
        db.commit()
        restantes = max(0, DOS_PASOS_MAX_INTENTOS - registro.intentos)
        raise AppError(400, f"El código ingresado es incorrecto. Intentos restantes: {restantes}.")

    registro.usado = True
    trusted_token = sesiones_service.crear_dispositivo_confiable(db, usuario, request) if confiar_dispositivo else None
    resultado = sesiones_service.crear_sesion(db, usuario, request, trusted_token)
    resultado["usuario"] = usuario_publico(usuario)
    db.commit()
    return resultado


def reenviar_codigo_login(db: Session, challenge_token: str) -> dict:
    payload = decodificar_token(challenge_token, error_sesion=False)
    if payload.get("purpose") != "login_2fa":
        raise AppError(400, "La solicitud de verificación no es válida.")
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(
        Usuario.id == payload.get("sub"), Usuario.estado == "ACTIVO"
    ).first()
    if usuario is None or usuario.rol.codigo not in ROLES_REQUIEREN_2FA:
        raise AppError(400, "La solicitud de verificación no es válida.")
    reciente = db.query(CodigoDosPasos).filter(
        CodigoDosPasos.usuario_id == usuario.id,
        CodigoDosPasos.creado_en > utcnow() - timedelta(seconds=30),
    ).first()
    if reciente:
        raise AppError(429, "Espera 30 segundos antes de solicitar otro código.")
    _emitir_codigo_2fa(db, usuario)
    return {"message": "Se envió un nuevo código de seguridad."}


def login(db: Session, email: str, password: str, request, trusted_device_token: str | None = None) -> dict:
    if not email or not password:
        raise AppError(400, "Correo y contraseña son obligatorios.")
    usuario = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.email == email.lower())
        .first()
    )
    if usuario is None or usuario.es_invitado:
        raise AppError(401, "Credenciales incorrectas.")

    ahora = utcnow()
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        minutos = int((usuario.bloqueado_hasta - ahora).total_seconds() // 60) + 1
        raise AppError(423, f"Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta de nuevo en {minutos} minuto(s).")
    if usuario.estado != "ACTIVO":
        raise AppError(403, "Esta cuenta se encuentra inactiva.")
    if not verificar_password(password, usuario.password_hash):
        intentos = usuario.intentos_fallidos + 1
        bloqueado = intentos >= settings.max_intentos_login
        usuario.intentos_fallidos = 0 if bloqueado else intentos
        usuario.bloqueado_hasta = ahora + timedelta(minutes=settings.bloqueo_minutos) if bloqueado else None
        db.commit()
        if bloqueado:
            raise AppError(423, f"Cuenta bloqueada temporalmente por {settings.bloqueo_minutos} minutos tras 5 intentos fallidos.")
        raise AppError(401, "Credenciales incorrectas.")
    if not usuario.email_verificado:
        raise AppError(403, "Debes verificar tu correo antes de iniciar sesión.", requiresVerification=True, email=usuario.email)

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    db.commit()
    return _preparar_acceso(db, usuario, request, trusted_device_token)


def login_con_google(db: Session, credential: str, request: Request | None = None, rol: str | None = None, numero_resolucion: str | None = None, acepta_politica: bool = False, trusted_device_token: str | None = None) -> dict:
    # Verifica con los servidores de Google que el token es real y no fue
    # falsificado, y que efectivamente fue emitido para nuestro Client ID.

    try:
        payload = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=30
        )
    except ValueError as exc:
        logger.warning("Google rechazó el token: %s", exc)
        raise AppError(401, "No se pudo validar tu cuenta de Google. Intenta de nuevo.")

    email = payload.get("email")
    if not email or not payload.get("email_verified", False):
        raise AppError(401, "No se pudo verificar el correo de la cuenta de Google.")
    nombre = (payload.get("given_name") or payload.get("name") or "Usuario").strip()
    apellido = (payload.get("family_name") or "Google").strip()
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.email == email.lower()).first()

    if usuario is None:
        if rol is None:
            return {"requiereRol": True, "email": email.lower(), "nombre": nombre, "apellido": apellido}
        if rol not in ROLES_AUTOREGISTRO:
            raise AppError(400, "El rol seleccionado no es válido.")
        numero_resolucion = _exigir_resolucion_psicologo(rol, numero_resolucion)
        _exigir_aceptacion_politica(acepta_politica)

        # Se le pone una contraseña aleatoria e inutilizable porque nunca la
        # va a necesitar (siempre entrará por Google).

        usuario = Usuario(
            nombre=nombre, apellido=apellido, email=email.lower(),
            password_hash=hash_password(secrets.token_urlsafe(32)),
            rol_id=_obtener_rol(db, rol).id,
            numero_resolucion=numero_resolucion,
            email_verificado=True,
            politica_version=POLITICA_DATOS_VERSION,
            politica_aceptada_en=utcnow(),
            estado="ACTIVO",

        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        auditoria_service.registrar_auditoria(
            db,
            usuario=usuario,
            accion="POLITICA_ACEPTADA",
            entidad="Usuario",
            entidad_id=str(usuario.id),
            request=request,
            nota=f"Versión {POLITICA_DATOS_VERSION}",
        )
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

    return _preparar_acceso(db, usuario, request, trusted_device_token)

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