import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_gestor, require_lector_reportes
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


# Encuestas realizadas por los trabajadores (avance por instrumento y niveles de riesgo).
# Solo para ADMINISTRADOR y EVALUADOR_SST; lo consume la sección "Encuestas realizadas" de Reportes.jsx
@router.get("/encuestas")
def listar_encuestas_realizadas(
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return reportes_service.listar_encuestas_realizadas(db, actual)


# Respuestas de un trabajador a cada pregunta (descifradas). Confidencial: solo gestores.
@router.get("/encuestas/{participante_id}/respuestas")
def respuestas_encuesta(
    participante_id: uuid.UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return reportes_service.respuestas_participante(db, actual, participante_id)
