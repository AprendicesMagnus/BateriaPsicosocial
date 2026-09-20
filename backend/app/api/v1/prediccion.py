from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import asegurar_acceso_organizacion, require_gestor
from app.core.errors import AppError
from app.db.session import get_db
from app.models.evaluation import Evaluacion
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
    evaluacion = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if evaluacion is None:
        raise AppError(404, "Evaluación no encontrada.")
    asegurar_acceso_organizacion(actual, evaluacion.organizacion_id)
    return prediccion_service.analizar_riesgo_predictivo(db, evaluacion_id, area_id)

