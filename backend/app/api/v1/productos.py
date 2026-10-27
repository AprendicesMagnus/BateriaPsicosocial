from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import ProductoCreate, ProductoUpdate
from app.services import productos as productos_service


router = APIRouter()


@router.get("")
def listar_productos(db: Session = Depends(get_db)):
    return productos_service.listar_productos(db, solo_activos=True)


@router.get("/admin")
def listar_productos_admin(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return productos_service.listar_productos(db, solo_activos=False)


@router.post("")
def crear_producto(
    data: ProductoCreate,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return productos_service.crear_producto(db, data)


@router.patch("/{producto_id}")
def actualizar_producto(
    producto_id: UUID,
    data: ProductoUpdate,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return productos_service.actualizar_producto(db, producto_id, data)


@router.delete("/{producto_id}")
def eliminar_producto(
    producto_id: UUID,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return productos_service.eliminar_producto(db, producto_id)
