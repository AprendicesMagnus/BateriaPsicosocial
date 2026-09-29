from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.catalog import Permiso, Rol, RolPermiso
from app.models.user import Usuario


def listar_roles(db: Session) -> list[dict]:
    roles = db.query(Rol).all()
    return [
        {
            "id": str(rol.id),
            "codigo": rol.codigo,
            "nombre": rol.nombre,
            "descripcion": rol.descripcion,
            "esSistema": rol.es_sistema,
            "activo": rol.activo,
            "permisos": [rp.permiso.codigo for rp in rol.permisos],
        }
        for rol in roles
    ]


def crear_rol(db: Session, data) -> dict:
    if db.query(Rol).filter(Rol.codigo == data.codigo.upper()).first():
        raise AppError(409, "Ya existe un rol con ese código.")
    rol = Rol(
        codigo=data.codigo.upper(),
        nombre=data.nombre,
        descripcion=data.descripcion,
        es_sistema=False,
        activo=True,
    )
    db.add(rol)
    db.flush()
    _asignar_permisos(db, rol, data.permisos)
    db.commit()
    return {"id": str(rol.id), "codigo": rol.codigo}


def actualizar_rol(db: Session, rol_id, data) -> dict:
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if rol is None:
        raise AppError(404, "Rol no encontrado.")
    if data.nombre is not None:
        rol.nombre = data.nombre
    if data.descripcion is not None:
        rol.descripcion = data.descripcion
    if data.activo is not None:
        if rol.codigo == "SUPER_ADMINISTRADOR" and data.activo is False:
            raise AppError(400, "No se puede desactivar el rol de administrador del sistema.")
        rol.activo = data.activo
    if data.permisos is not None:
        db.query(RolPermiso).filter(RolPermiso.rol_id == rol.id).delete()
        _asignar_permisos(db, rol, data.permisos)
    db.commit()
    return {"id": str(rol.id), "codigo": rol.codigo}


def eliminar_rol(db: Session, rol_id) -> dict:
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if rol is None:
        raise AppError(404, "Rol no encontrado.")
    if rol.es_sistema or rol.codigo == "SUPER_ADMINISTRADOR":
        raise AppError(400, "No se puede eliminar el rol de administrador del sistema.")
    if db.query(Usuario).filter(Usuario.rol_id == rol.id).first():
        raise AppError(400, "No se puede eliminar un rol asignado a usuarios.")
    db.delete(rol)
    db.commit()
    return {"message": "Rol eliminado."}


def _asignar_permisos(db: Session, rol: Rol, codigos: list[str]) -> None:
    if not codigos:
        return
    permisos = db.query(Permiso).filter(Permiso.codigo.in_(codigos)).all()
    encontrados = {p.codigo for p in permisos}
    faltantes = set(codigos) - encontrados
    if faltantes:
        raise AppError(400, f"Permisos no válidos: {', '.join(sorted(faltantes))}")
    for permiso in permisos:
        db.add(RolPermiso(rol_id=rol.id, permiso_id=permiso.id))
