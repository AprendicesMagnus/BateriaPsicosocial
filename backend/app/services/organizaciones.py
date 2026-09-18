from sqlalchemy.orm import Session

from app.api.deps import asegurar_acceso_organizacion
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante
from app.models.organization import Area, Organizacion
from app.models.user import Usuario


def listar_organizaciones(db: Session, actual: Usuario) -> list[Organizacion]:
    query = db.query(Organizacion)
    if actual.rol.codigo != "ADMINISTRADOR":
        query = query.filter(Organizacion.id == actual.organizacion_id)
    return query.order_by(Organizacion.nombre.asc()).all()


def existe_organizacion_nit(db: Session, nit: str) -> dict:
    nit_limpio = nit.strip()
    org = db.query(Organizacion).filter(Organizacion.nit == nit_limpio).first()
    if org:
        return {"existe": True, "organizacionId": str(org.id)}
    return {"existe": False, "organizacionId": None}


from app.core.crypto import email_valido, hash_password, password_valida
from app.models.user import Rol, Usuario
from app.services.auth import crear_y_enviar_codigo


def autorregistrar_organizacion(db: Session, data) -> dict:
    """Registra de forma atómica una empresa y su primer usuario (EVALUADOR_SST).

    Garantías de Seguridad y Diseño:
    1. Se asigna el rol EVALUADOR_SST (no ADMINISTRADOR global) para evitar exposición
       de datos entre empresas.
    2. Si falla cualquier validación (NIT o Email duplicado, clave débil), se revierte
       toda la transacción sin dejar huérfanos.
    3. Se genera y envía el código de verificación de correo electrónico obligando
       a verificar la cuenta antes del login.
    """
    nit_limpio = data.nit.strip()
    if db.query(Organizacion).filter(Organizacion.nit == nit_limpio).first():
        raise AppError(409, "Ya existe una organización registrada con este NIT.")

    email_usuario = str(data.usuarioEmail).lower().strip()
    if not data.usuarioNombre or not data.usuarioApellido or not email_usuario or not data.usuarioPassword:
        raise AppError(400, "Todos los datos del usuario responsable de la empresa son obligatorios.")

    if not email_valido(email_usuario):
        raise AppError(400, "El correo electrónico del usuario no es válido.")

    if not password_valida(data.usuarioPassword):
        raise AppError(
            400,
            "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números.",
        )

    if db.query(Usuario).filter(Usuario.email == email_usuario).first():
        raise AppError(409, "Ya existe una cuenta registrada con este correo electrónico.")

    rol_evaluador = db.query(Rol).filter(Rol.codigo == "EVALUADOR_SST").first()
    if rol_evaluador is None:
        raise AppError(500, "El catálogo de roles (EVALUADOR_SST) no está inicializado.")

    org = Organizacion(
        nombre=data.nombre.strip(),
        nit=nit_limpio,
        sector=data.sector,
        municipio=data.municipio,
        email=str(data.email) if data.email else None,
        telefono=data.telefono,
        activa=True,
    )
    db.add(org)
    db.flush()

    usuario = Usuario(
        nombre=data.usuarioNombre.strip(),
        apellido=data.usuarioApellido.strip(),
        email=email_usuario,
        password_hash=hash_password(data.usuarioPassword),
        rol_id=rol_evaluador.id,
        organizacion_id=org.id,
        email_verificado=False,
        estado="ACTIVO",
    )
    db.add(usuario)
    db.commit()

    db.refresh(org)
    db.refresh(usuario)

    crear_y_enviar_codigo(db, usuario, "VERIFICACION_EMAIL")

    return {
        "message": "Empresa y cuenta creadas con éxito. Revisa tu correo para verificar tu cuenta.",
        "organizacionId": str(org.id),
        "usuarioId": str(usuario.id),
        "email": usuario.email,
        "rol": rol_evaluador.codigo,
    }


def crear_organizacion(db: Session, data) -> Organizacion:
    if db.query(Organizacion).filter(Organizacion.nit == data.nit).first():
        raise AppError(409, "Ya existe una organización con ese NIT.")
    org = Organizacion(
        nombre=data.nombre.strip(),
        nit=data.nit.strip(),
        sector=data.sector,
        municipio=data.municipio,
        telefono=data.telefono,
        email=str(data.email) if data.email else None,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def actualizar_organizacion(db: Session, org_id, data) -> Organizacion:
    org = db.query(Organizacion).filter(Organizacion.id == org_id).first()
    if org is None:
        raise AppError(404, "Organización no encontrada.")
    for campo, valor in {
        "nombre": data.nombre,
        "nit": data.nit,
        "sector": data.sector,
        "municipio": data.municipio,
        "telefono": data.telefono,
        "activa": data.activa,
    }.items():
        if valor is not None:
            setattr(org, campo, valor.strip() if isinstance(valor, str) else valor)
    if data.email is not None:
        org.email = str(data.email)
    db.commit()
    db.refresh(org)
    return org


def listar_areas(db: Session, organizacion_id, actual: Usuario) -> list[Area]:
    asegurar_acceso_organizacion(actual, organizacion_id)
    return db.query(Area).filter(Area.organizacion_id == organizacion_id).order_by(Area.nombre.asc()).all()


def crear_area(db: Session, data, actual: Usuario) -> Area:
    asegurar_acceso_organizacion(actual, data.organizacionId)
    if db.query(Organizacion).filter(Organizacion.id == data.organizacionId).first() is None:
        raise AppError(404, "Organización no encontrada.")
    existe = (
        db.query(Area)
        .filter(Area.organizacion_id == data.organizacionId, Area.nombre == data.nombre.strip())
        .first()
    )
    if existe:
        raise AppError(409, "Ya existe un área con ese nombre en la organización.")
    area = Area(organizacion_id=data.organizacionId, nombre=data.nombre.strip(), activa=True)
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


def actualizar_area(db: Session, area_id, data, actual: Usuario) -> Area:
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise AppError(404, "Área no encontrada.")
    asegurar_acceso_organizacion(actual, area.organizacion_id)
    if data.nombre is not None:
        area.nombre = data.nombre.strip()
    if data.activa is not None:
        area.activa = data.activa
    db.commit()
    db.refresh(area)
    return area


def eliminar_area(db: Session, area_id, actual: Usuario) -> dict:
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise AppError(404, "Área no encontrada.")
    asegurar_acceso_organizacion(actual, area.organizacion_id)
    if db.query(Usuario).filter(Usuario.area_id == area.id).first():
        raise AppError(400, "No se puede eliminar un área que tiene trabajadores asociados.")
    participantes = (
        db.query(EvaluacionParticipante)
        .join(Usuario, Usuario.id == EvaluacionParticipante.trabajador_id)
        .filter(Usuario.area_id == area.id)
        .first()
    )
    if participantes:
        raise AppError(400, "No se puede eliminar un área que tiene evaluaciones asociadas.")
    db.delete(area)
    db.commit()
    return {"message": "Área eliminada."}
