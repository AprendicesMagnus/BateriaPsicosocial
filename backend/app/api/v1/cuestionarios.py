from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_gestor
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import CuestionarioCreate
from app.services import cuestionarios as cuestionarios_service

router = APIRouter()


class PreguntaActualizarRequest(BaseModel):
    enunciado: str | None = Field(default=None, min_length=5, max_length=2000)
    inversa: bool | None = None


@router.get("")
def listar_cuestionarios(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(get_current_user),
):
    return cuestionarios_service.listar_cuestionarios(db)


@router.get("/{version_id}")
def obtener_cuestionario(
    version_id: UUID,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(get_current_user),
):
    return cuestionarios_service.obtener_cuestionario(db, version_id)


@router.post("")
def crear_cuestionario(
    data: CuestionarioCreate,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_gestor),
):
    return cuestionarios_service.crear_cuestionario(db, data)


@router.patch("/preguntas/{pregunta_id}")
def actualizar_pregunta(
    pregunta_id: UUID,
    data: PreguntaActualizarRequest,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_gestor),
):
    return cuestionarios_service.actualizar_pregunta(db, pregunta_id, data.enunciado, data.inversa)


@router.delete("/preguntas/{pregunta_id}")
def eliminar_pregunta(
    pregunta_id: UUID,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_gestor),
):
    return cuestionarios_service.eliminar_pregunta(db, pregunta_id)
