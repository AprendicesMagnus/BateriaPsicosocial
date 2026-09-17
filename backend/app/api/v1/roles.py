from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import RolCreate, RolUpdate
from app.services import roles as roles_service

router = APIRouter()


@router.get("")
def listar_roles(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return roles_service.listar_roles(db)


@router.post("")
def crear_rol(
    data: RolCreate,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return roles_service.crear_rol(db, data)


@router.patch("/{rol_id}")
def actualizar_rol(
    rol_id: UUID,
    data: RolUpdate,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return roles_service.actualizar_rol(db, rol_id, data)


@router.delete("/{rol_id}")
def eliminar_rol(
    rol_id: UUID,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return roles_service.eliminar_rol(db, rol_id)
