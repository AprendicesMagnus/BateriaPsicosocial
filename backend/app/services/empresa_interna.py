"""Gestión de la organización interna de la plataforma MAGNUS | SIG."""

from sqlalchemy.orm import Session

from app.models.organization import Organizacion
from app.models.user import Rol, Usuario

EMPRESA_INTERNA_NOMBRE = "MAGNUS | SIG"
EMPRESA_INTERNA_NIT = "1075277687-2"


def obtener_empresa_interna(db: Session) -> Organizacion:
    """Obtiene o crea MAGNUS | SIG de forma idempotente, sin duplicarla."""
    organizacion = (
        db.query(Organizacion)
        .filter(Organizacion.nit == EMPRESA_INTERNA_NIT)
        .first()
    )

    if organizacion is None:
        # Recupera un registro previo por nombre si existiera con otro NIT.
        organizacion = (
            db.query(Organizacion)
            .filter(Organizacion.nombre.ilike(EMPRESA_INTERNA_NOMBRE))
            .first()
        )
        if organizacion is not None:
            duplicado = (
                db.query(Organizacion)
                .filter(
                    Organizacion.nit == EMPRESA_INTERNA_NIT,
                    Organizacion.id != organizacion.id,
                )
                .first()
            )
            if duplicado is not None:
                raise ValueError("El NIT de MAGNUS | SIG ya está asociado a otra empresa.")
            organizacion.nit = EMPRESA_INTERNA_NIT
        else:
            organizacion = Organizacion(
                nombre=EMPRESA_INTERNA_NOMBRE,
                nit=EMPRESA_INTERNA_NIT,
                activa=True,
            )
            db.add(organizacion)
    else:
        # Mantiene un nombre uniforme en Perfil, Panel y selectores.
        organizacion.nombre = EMPRESA_INTERNA_NOMBRE
        organizacion.activa = True

    db.flush()
    return organizacion


def asignar_empresa_a_superadministradores(db: Session, organizacion: Organizacion | None = None) -> Organizacion:
    """Asocia MAGNUS | SIG a todos los superadministradores sin cambiar sus roles."""
    organizacion = organizacion or obtener_empresa_interna(db)
    super_admin_ids = (
        db.query(Usuario.id)
        .join(Rol, Usuario.rol_id == Rol.id)
        .filter(Rol.codigo == "SUPER_ADMINISTRADOR")
        .all()
    )
    ids = [fila[0] for fila in super_admin_ids]
    if ids:
        db.query(Usuario).filter(Usuario.id.in_(ids)).update(
            {Usuario.organizacion_id: organizacion.id},
            synchronize_session=False,
        )
    return organizacion
