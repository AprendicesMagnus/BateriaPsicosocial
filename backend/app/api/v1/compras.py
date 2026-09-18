from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import Usuario
from app.schemas.common import CompraCreate
from app.services import compras as compras_service

router = APIRouter()


@router.post("")
def crear_compra(
    data: CompraCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return compras_service.crear_compra(db, data, actual)


@router.get("/usuario/{usuario_id}")
def listar_compras_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return compras_service.listar_compras_usuario(db, usuario_id, actual)


@router.get("/{compra_id}")
def obtener_compra(
    compra_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return compras_service.obtener_compra(db, compra_id, actual)
