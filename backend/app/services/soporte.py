from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.correo import enviar_correo
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


def notificar_ticket(ticket: dict, email_usuario: str) -> None:
    """Envía el mensaje del Centro de ayuda al buzón de soporte. Se ejecuta en segundo plano:
    si el correo falla, el ticket ya quedó guardado y el Super Administrador puede verlo igual."""
    settings = get_settings()
    destino = settings.soporte_email or settings.admin_email
    if not destino:
        return
    asunto = f"[Soporte MAGNUS|SIG] Mensaje de {ticket.get('usuarioNombre') or 'un usuario'}"
    contenido = (
        "Nuevo mensaje desde el Centro de ayuda\n\n"
        f"De: {ticket.get('usuarioNombre')} <{email_usuario}>\n"
        f"Rol: {ticket.get('usuarioRol')}\n"
        f"Fecha: {ticket.get('creadoEn')}\n\n"
        f"Mensaje:\n{ticket.get('mensaje')}\n\n"
        f"Para responder, escribe a {email_usuario}."
    )
    enviar_correo(destino, asunto, contenido)
