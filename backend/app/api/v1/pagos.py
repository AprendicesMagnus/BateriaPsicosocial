from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import Usuario
from app.schemas.common import PagoCreate
from app.services import compras as compras_service

router = APIRouter()


@router.post("")
def procesar_pago(
    data: PagoCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return compras_service.procesar_pago(db, data, actual)
