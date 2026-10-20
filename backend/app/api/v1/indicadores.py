from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.core.errors import AppError
from app.core.roles import ROLES_EVALUADOR, ROLES_DIRECCION
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
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
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
    if actual.rol.codigo not in {"SUPER_ADMINISTRADOR", *ROLES_EVALUADOR, *ROLES_DIRECCION}:
        raise AppError(403, "No tiene permisos para consultar el histórico comparativo.")
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
        org_target = actual.organizacion_id

    return indicadores_service.obtener_historico_indicadores(db, org_target, dim_target)


@router.get("/por-categoria")
def obtener_indicadores_por_categoria(
    organizacion_id: UUID | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
        organizacion_id = actual.organizacion_id

    return indicadores_service.obtener_distribucion_por_categoria(db, organizacion_id)


@router.get("/mapa-calor")
def obtener_mapa_calor(
    organizacion_id: UUID | None = None,
    codigo: str | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    if actual.rol.codigo not in {"SUPER_ADMINISTRADOR", *ROLES_EVALUADOR, *ROLES_DIRECCION}:
        raise AppError(403, "No tiene permisos para consultar el mapa de calor por área.")
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
        organizacion_id = actual.organizacion_id

    return indicadores_service.obtener_mapa_calor(db, organizacion_id, codigo)


@router.get("/grupos")
def obtener_analisis_grupos(
    organizacion_id: UUID | None = None,
    codigo: str | None = None,
    variable: str = "sexo",
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    if actual.rol.codigo not in {"SUPER_ADMINISTRADOR", *ROLES_EVALUADOR}:
        raise AppError(403, "No tiene permisos para consultar el análisis por grupos.")
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
        organizacion_id = actual.organizacion_id

    return indicadores_service.obtener_analisis_grupos(db, organizacion_id, codigo, variable)



