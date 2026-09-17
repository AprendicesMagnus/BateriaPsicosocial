from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.services import auditoria as auditoria_service

router = APIRouter()


@router.get("")
def listar_auditoria(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return auditoria_service.listar_auditoria(db)
