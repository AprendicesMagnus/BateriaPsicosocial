from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import PlanCreate, PlanUpdate
from app.services import auditoria as auditoria_service
from app.services import planes as planes_service

router = APIRouter()


@router.get("")
def listar_planes_publicos(db: Session = Depends(get_db)):
    """Público (Landing): solo los planes activos, de menor a mayor cantidad."""
    return planes_service.listar_planes(db, solo_activos=True)


@router.get("/admin")
def listar_planes_admin(db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return planes_service.listar_planes(db, solo_activos=False)


@router.post("")
def crear_plan(data: PlanCreate, request: Request, db: Session = Depends(get_db), actual: Usuario = Depends(require_admin)):
    plan = planes_service.crear_plan(db, data)
    auditoria_service.registrar_auditoria(
        db, usuario=actual, accion="CREAR_PLAN", entidad="Plan", entidad_id=plan["id"], request=request
    )
    return plan


@router.patch("/{plan_id}")
def actualizar_plan(
    plan_id: UUID, data: PlanUpdate, request: Request, db: Session = Depends(get_db), actual: Usuario = Depends(require_admin)
):
    plan = planes_service.actualizar_plan(db, plan_id, data)
    auditoria_service.registrar_auditoria(
        db, usuario=actual, accion="EDITAR_PLAN", entidad="Plan", entidad_id=str(plan_id), request=request
    )
    return plan


@router.delete("/{plan_id}")
def eliminar_plan(plan_id: UUID, request: Request, db: Session = Depends(get_db), actual: Usuario = Depends(require_admin)):
    resultado = planes_service.eliminar_plan(db, plan_id)
    auditoria_service.registrar_auditoria(
        db, usuario=actual, accion="ELIMINAR_PLAN", entidad="Plan", entidad_id=str(plan_id), request=request
    )
    return resultado
