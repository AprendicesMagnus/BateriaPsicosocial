from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import Usuario
from app.schemas.common import PagoPedidoProductoCreate, PedidoProductoCreate
from app.services import pedidos_productos as pedidos_service


router = APIRouter()


@router.post("")
def crear_pedido(
    data: PedidoProductoCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return pedidos_service.crear_pedido(db, data, actual)


@router.get("/usuario/{usuario_id}")
def listar_pedidos_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return pedidos_service.listar_pedidos_usuario(db, usuario_id, actual)


@router.post("/pago")
def procesar_pago(
    data: PagoPedidoProductoCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return pedidos_service.procesar_pago(db, data, actual)


@router.get("/{pedido_id}")
def obtener_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return pedidos_service.obtener_pedido(db, pedido_id, actual)


@router.post("/{pedido_id}/wompi/checkout")
def preparar_checkout_wompi(
    pedido_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return pedidos_service.preparar_checkout_wompi(db, pedido_id, actual)


@router.post("/{pedido_id}/cancelar")
def cancelar_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return pedidos_service.cancelar_pedido(db, pedido_id, actual)
