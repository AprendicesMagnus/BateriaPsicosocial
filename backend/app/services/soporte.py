from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.models.ticket_soporte import TicketSoporte
from app.models.user import Usuario


def _publico(ticket: TicketSoporte) -> dict:
    return {
        "id": str(ticket.id),
        "usuarioId": str(ticket.usuario_id),
        "usuarioNombre": f"{ticket.usuario.nombre} {ticket.usuario.apellido}".strip() if ticket.usuario else None,
        "usuarioRol": ticket.usuario.rol.codigo if ticket.usuario else None,
        "mensaje": ticket.mensaje,
        "estado": ticket.estado,
        "creadoEn": ticket.creado_en.isoformat(),
    }


def crear_ticket(db: Session, usuario: Usuario, mensaje: str) -> dict:
    mensaje = mensaje.strip()
    if not mensaje or len(mensaje) > 2000:
        raise AppError(400, "El mensaje no puede estar vacío ni superar los 2000 caracteres.")
    ticket = TicketSoporte(usuario_id=usuario.id, mensaje=mensaje)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    ticket.usuario = usuario
    return _publico(ticket)


def listar_tickets(db: Session) -> list[dict]:
    """Solo Super Administrador (ver api/v1/soporte.py)."""
    tickets = (
        db.query(TicketSoporte)
        .options(joinedload(TicketSoporte.usuario).joinedload(Usuario.rol))
        .order_by(TicketSoporte.creado_en.desc())
        .all()
    )
    return [_publico(t) for t in tickets]


def marcar_resuelto(db: Session, ticket_id) -> dict:
    ticket = db.query(TicketSoporte).filter(TicketSoporte.id == ticket_id).first()
    if ticket is None:
        raise AppError(404, "Ticket no encontrado.")
    ticket.estado = "RESUELTO"
    db.commit()
    db.refresh(ticket)
    return _publico(ticket)
