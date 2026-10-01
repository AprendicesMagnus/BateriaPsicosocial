from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_lector_reportes
from app.db.session import get_db
from app.models.user import Usuario
from app.services import reportes as reportes_service

router = APIRouter()


@router.get("")
def listar_reportes(
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_lector_reportes),
):
    return reportes_service.listar_reportes_por_area(db, actual)
