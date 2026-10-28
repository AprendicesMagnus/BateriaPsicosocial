from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.crypto import utcnow
from app.core.errors import AppError
from app.services.correo import enviar_correo
from app.services.notificaciones import notificar
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
        "respuesta": ticket.respuesta,
        "respondidoEn": ticket.respondido_en.isoformat() if ticket.respondido_en else None,
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


def listar_tickets_usuario(db: Session, usuario_id) -> list[dict]:
    tickets = (
        db.query(TicketSoporte)
        .options(joinedload(TicketSoporte.usuario).joinedload(Usuario.rol))
        .filter(TicketSoporte.usuario_id == usuario_id)
        .order_by(TicketSoporte.creado_en.desc())
        .all()
    )
    return [_publico(t) for t in tickets]


def responder_ticket(db: Session, ticket_id, respuesta: str, respondido_por=None) -> dict:
    ticket = db.query(TicketSoporte).filter(TicketSoporte.id == ticket_id).first()
    if ticket is None:
        raise AppError(404, "Ticket no encontrado.")
    respuesta = respuesta.strip()
    if not respuesta:
        raise AppError(400, "La respuesta no puede estar vacía.")
    ticket.respuesta = respuesta
    ticket.respondido_en = utcnow()
    ticket.estado = "RESUELTO"
    if respondido_por is None or (respondido_por != ticket.usuario_id and str(respondido_por) != str(ticket.usuario_id)):
        notificar(
            db,
            usuario_id=ticket.usuario_id,
            tipo="SOPORTE_RESPONDIDO",
            titulo="Respuesta a tu mensaje de soporte",
            mensaje="El equipo de soporte respondió tu mensaje. Puedes verlo en el Centro de ayuda, en la sección Mis mensajes.",
            commit=False,
        )
    db.commit()
    db.refresh(ticket)
    return _publico(ticket)


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
