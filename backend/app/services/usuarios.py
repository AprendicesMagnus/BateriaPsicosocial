from sqlalchemy.orm import Session, joinedload

from app.core.crypto import hash_password, password_valida
from app.core.errors import AppError
from app.models.organization import Area, Organizacion
from app.models.user import Rol, Usuario
from app.services.auth import usuario_publico


def listar_usuarios(db: Session, actual: Usuario) -> list[dict]:
    query = db.query(Usuario).options(joinedload(Usuario.rol))
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
        if actual.organizacion_id is None:
            return []
        query = query.filter(Usuario.organizacion_id == actual.organizacion_id)
    return [usuario_publico(u) for u in query.order_by(Usuario.fecha_registro.desc()).all()]


def crear_usuario(db: Session, data, actual: Usuario) -> dict:
    if db.query(Usuario).filter(Usuario.email == str(data.email).lower()).first():
        raise AppError(409, "Ya existe una cuenta registrada con este correo.")
    if not password_valida(data.password):
        raise AppError(
            400,
            "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números.",
        )
    rol = db.query(Rol).filter(Rol.codigo == data.rolCodigo, Rol.activo.is_(True)).first()
    if rol is None:
        raise AppError(400, "El rol indicado no existe o no está activo.")
    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and data.organizacionId != actual.organizacion_id:
        raise AppError(403, "No puede crear usuarios de otra organización.")

    if data.numeroIdentificacion and data.organizacionId:
        duplicado = (
            db.query(Usuario)
            .filter(
                Usuario.organizacion_id == data.organizacionId,
                Usuario.numero_identificacion == data.numeroIdentificacion,
            )
            .first()
        )
        if duplicado:
            raise AppError(409, "El número de identificación ya está registrado en la organización.")

    if data.areaId:
        area = db.query(Area).filter(Area.id == data.areaId).first()
        if area is None or area.organizacion_id != data.organizacionId:
            raise AppError(400, "El área no pertenece a la organización indicada.")

    usuario = Usuario(
        nombre=data.nombre.strip(),
        apellido=data.apellido.strip(),
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        rol_id=rol.id,
        organizacion_id=data.organizacionId,
        area_id=data.areaId,
        numero_identificacion=data.numeroIdentificacion,
        cargo=data.cargo,
        email_verificado=True,
        estado="ACTIVO",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario.id).one()
    return usuario_publico(usuario)


def actualizar_usuario(db: Session, usuario_id, data, actual: Usuario) -> dict:
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise AppError(404, "Usuario no encontrado.")
    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and usuario.organizacion_id != actual.organizacion_id:
        raise AppError(403, "No tiene acceso a este usuario.")

    if data.rolCodigo:
        rol = db.query(Rol).filter(Rol.codigo == data.rolCodigo, Rol.activo.is_(True)).first()
        if rol is None:
            raise AppError(400, "El rol indicado no existe o no está activo.")
        usuario.rol_id = rol.id
    if data.nombre is not None:
        usuario.nombre = data.nombre.strip()
    if data.apellido is not None:
        usuario.apellido = data.apellido.strip()
    if data.estado is not None:
        if data.estado not in {"ACTIVO", "INACTIVO"}:
            raise AppError(400, "El estado no es válido.")
        usuario.estado = data.estado
    if data.organizacionId is not None:
        usuario.organizacion_id = data.organizacionId
    if data.areaId is not None:
        usuario.area_id = data.areaId
    if data.numeroIdentificacion is not None:
        usuario.numero_identificacion = data.numeroIdentificacion
    if data.cargo is not None:
        usuario.cargo = data.cargo
    db.commit()
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario.id).one()
    return usuario_publico(usuario)


def desactivar_usuario(db: Session, usuario_id, actual: Usuario) -> dict:
    class _Data:
        estado = "INACTIVO"
        nombre = None
        apellido = None
        rolCodigo = None
        organizacionId = None
        areaId = None
        numeroIdentificacion = None
        cargo = None

    return actualizar_usuario(db, usuario_id, _Data(), actual)


def listar_trabajadores(db: Session, organizacion_id, actual: Usuario) -> list[dict]:
    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and actual.organizacion_id != organizacion_id:
        raise AppError(403, "No tiene acceso a esta organización.")
    trabajadores = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .join(Rol)
        .filter(Usuario.organizacion_id == organizacion_id, Rol.codigo == "TRABAJADOR")
        .all()
    )
    return [usuario_publico(u) for u in trabajadores]


def cambiar_rol_usuario(db: Session, usuario_id, rol_codigo: str, actual: Usuario) -> dict:
    """Cambia el rol de un usuario existente.

    Restricciones:
    - Solo ADMINISTRADOR puede invocar esta función (la verifica el router).
    - El rol_codigo debe existir y estar activo.
    - No se permite quitar el rol ADMINISTRADOR al único administrador activo del sistema.
    """
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise AppError(404, "Usuario no encontrado.")

    nuevo_rol = db.query(Rol).filter(Rol.codigo == rol_codigo, Rol.activo.is_(True)).first()
    if nuevo_rol is None:
        raise AppError(400, f"El rol '{rol_codigo}' no existe o no está activo.")

    # Protección: no permitir que el único administrador activo se quite ese rol
    if usuario.rol.codigo == "SUPER_ADMINISTRADOR" and rol_codigo != "SUPER_ADMINISTRADOR":
        conteo_admins_activos = (
            db.query(Usuario)
            .join(Rol)
            .filter(
                Rol.codigo == "SUPER_ADMINISTRADOR",
                Usuario.estado == "ACTIVO",
                Usuario.id != usuario_id,
            )
            .count()
        )
        if conteo_admins_activos == 0:
            raise AppError(
                409,
                "No es posible quitar el rol de Administrador a este usuario porque es el "
                "único administrador activo del sistema. Asigna primero el rol a otro usuario.",
            )

    rol_anterior = usuario.rol.codigo
    usuario.rol_id = nuevo_rol.id
    db.commit()
    usuario = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.id == usuario.id).one()
    return {**usuario_publico(usuario), "rol_anterior": rol_anterior}

