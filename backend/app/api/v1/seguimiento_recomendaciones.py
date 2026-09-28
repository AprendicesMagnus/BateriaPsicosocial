from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.services import seguimiento_recomendaciones as seguimiento_service

router = APIRouter()


class SeguimientoCreateUpdate(BaseModel):
    organizacionId: UUID | None = None
    recomendacionId: UUID
    estado: str = Field(..., description="PENDIENTE, EN_PROGRESO o IMPLEMENTADA")
    responsable: str | None = None
    notas: str | None = None


@router.get("")
def listar_seguimientos(
    organizacion_id: UUID | None = None,
    organizacionId: UUID | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    org_target = organizacion_id or organizacionId or actual.organizacion_id
    return seguimiento_service.listar_seguimientos(db, org_target, actual)


@router.post("")
def crear_o_actualizar_seguimiento(
    body: SeguimientoCreateUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    org_target = body.organizacionId or actual.organizacion_id
    return seguimiento_service.crear_o_actualizar_estado(
        db,
        organizacion_id=org_target,
        recomendacion_id=body.recomendacionId,
        estado=body.estado,
        actual=actual,
        responsable=body.responsable,
        notas=body.notas,
    )
