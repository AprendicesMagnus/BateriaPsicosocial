from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.services import panel as panel_service

router = APIRouter()


@router.get("")
def obtener_panel(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    """Solo Super Administrador. Datos del panel de administración."""
    return panel_service.obtener_panel(db)
