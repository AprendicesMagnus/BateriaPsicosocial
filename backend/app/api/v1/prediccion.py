from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_gestor
from app.db.session import get_db
from app.models.user import Usuario
from app.services import prediccion as prediccion_service

router = APIRouter()

@router.get("/evaluaciones/{evaluacion_id}/prediccion")
def obtener_analisis_predictivo(
    evaluacion_id: UUID,
    area_id: UUID | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return prediccion_service.analizar_riesgo_predictivo(db, evaluacion_id, area_id)
