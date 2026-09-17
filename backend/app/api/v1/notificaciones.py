from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.services import notificaciones as notificaciones_service

router = APIRouter()


@router.get("")
def listar_notificaciones(
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return notificaciones_service.listar_notificaciones(db, actual.id)


@router.post("/{notificacion_id}/leida")
def marcar_leida(
    notificacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return notificaciones_service.marcar_leida(db, notificacion_id, actual.id)
