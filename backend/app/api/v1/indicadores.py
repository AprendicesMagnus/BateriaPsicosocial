from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.services import indicadores as indicadores_service

router = APIRouter()

@router.get("")
def obtener_indicadores(
    organizacion_id: UUID | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    # Si es trabajador/evaluador restringir a su organizacion si no especifica
    if actual.rol.codigo != "ADMINISTRADOR":
        organizacion_id = actual.organizacion_id

    return indicadores_service.obtener_resumen_indicadores(db, organizacion_id)


@router.get("/historico")
def obtener_historico_indicadores(
    organizacion_id: UUID | None = None,
    organizacionId: UUID | None = None,
    dimension_id: UUID | None = None,
    dimensionId: UUID | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    org_target = organizacion_id or organizacionId
    dim_target = dimension_id or dimensionId
    if actual.rol.codigo != "ADMINISTRADOR":
        org_target = actual.organizacion_id

    return indicadores_service.obtener_historico_indicadores(db, org_target, dim_target)


@router.get("/por-categoria")
def obtener_indicadores_por_categoria(
    organizacion_id: UUID | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    if actual.rol.codigo != "ADMINISTRADOR":
        organizacion_id = actual.organizacion_id

    return indicadores_service.obtener_distribucion_por_categoria(db, organizacion_id)
