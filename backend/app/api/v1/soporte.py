from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import SoporteItemCreate, SoporteItemUpdate, TicketSoporteCreate, TicketSoporteRespuesta
from app.services import soporte as soporte_service
from app.services import soporte_contenido as contenido_service

router = APIRouter()


@router.post("")
def crear_ticket(
    data: TicketSoporteCreate,
    segundo_plano: BackgroundTasks,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    """Cualquier usuario autenticado envía un mensaje desde el Centro de ayuda."""
    ticket = soporte_service.crear_ticket(db, actual, data.mensaje)
    # El correo al buzón de soporte sale en segundo plano para no hacer esperar al usuario.
    segundo_plano.add_task(soporte_service.notificar_ticket, ticket, actual.email)
    return ticket



@router.get("/mios")
def listar_mis_tickets(db: Session = Depends(get_db), actual: Usuario = Depends(get_current_user)):
    return soporte_service.listar_tickets_usuario(db, actual.id)


@router.get("")
def listar_tickets(db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    """Solo el Super Administrador ve los tickets (p. ej. desde el Panel)."""
    return soporte_service.listar_tickets(db)


@router.post("/{ticket_id}/resolver")
def marcar_resuelto(ticket_id: UUID, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return soporte_service.marcar_resuelto(db, ticket_id)


@router.post("/{ticket_id}/responder")
def responder_ticket(
    ticket_id: UUID,
    data: TicketSoporteRespuesta,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return soporte_service.responder_ticket(db, ticket_id, data.respuesta)


# --- Contenido editable del Centro de ayuda ---------------------------------------------------


@router.get("/contenido")
def contenido_publico(db: Session = Depends(get_db), _actual: Usuario = Depends(get_current_user)):
    """Guías, preguntas frecuentes, glosario, etc. visibles para cualquier usuario con sesión."""
    return contenido_service.contenido_publico(db)


@router.get("/contenido/admin")
def contenido_admin(db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.listar_admin(db)


@router.post("/contenido")
def crear_contenido(data: SoporteItemCreate, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.crear_item(db, data)


@router.patch("/contenido/{item_id}")
def editar_contenido(item_id: UUID, data: SoporteItemUpdate, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.actualizar_item(db, item_id, data)


@router.delete("/contenido/{item_id}")
def eliminar_contenido(item_id: UUID, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.eliminar_item(db, item_id)
