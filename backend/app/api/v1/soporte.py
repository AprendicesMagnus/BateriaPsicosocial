from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import TicketSoporteCreate
from app.services import soporte as soporte_service

router = APIRouter()


@router.post("")
def crear_ticket(
    data: TicketSoporteCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    """Cualquier usuario autenticado envía un mensaje desde el Centro de ayuda."""
    return soporte_service.crear_ticket(db, actual, data.mensaje)


@router.get("")
def listar_tickets(db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    """Solo el Super Administrador ve los tickets (p. ej. desde el Panel)."""
    return soporte_service.listar_tickets(db)


@router.post("/{ticket_id}/resolver")
def marcar_resuelto(ticket_id: UUID, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return soporte_service.marcar_resuelto(db, ticket_id)
