"""Derechos del titular: exportacion de los datos propios y solicitud de eliminacion de la cuenta."""

from sqlalchemy.orm import Session

from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.audit import Auditoria
from app.models.commercial import Compra
from app.models.organization import Organizacion
from app.models.product_order import PedidoProducto
from app.models.ticket_soporte import TicketSoporte
from app.models.user import Usuario
from app.services import soporte as soporte_service
from app.services.pedidos_productos import _pedido_publico

# Texto fijo con el que empieza el mensaje del Centro de ayuda que representa la solicitud.
PREFIJO_SOLICITUD_ELIMINACION = "Solicitud de eliminación de cuenta."
LIMITE_REGISTRO_ACTIVIDAD = 500


def _iso(valor) -> str | None:
    return valor.isoformat() if valor else None


def nombre_archivo_datos() -> str:
    return f"mis-datos-magnussig-{utcnow():%Y%m%d}.json"


def exportar_datos(db: Session, usuario: Usuario) -> dict:
    """Reune solo los datos que pertenecen al usuario. No incluye contraseña, codigos ni datos de terceros."""
    empresas = (
        db.query(Organizacion)
        .filter(Organizacion.creada_por_id == usuario.id)
        .order_by(Organizacion.creado_en)
        .all()
    )
    compras = db.query(Compra).filter(Compra.usuario_id == usuario.id).order_by(Compra.creado_en).all()
    pedidos = (
        db.query(PedidoProducto)
        .filter(PedidoProducto.usuario_id == usuario.id)
        .order_by(PedidoProducto.creado_en)
        .all()
    )
    mensajes = (
        db.query(TicketSoporte)
        .filter(TicketSoporte.usuario_id == usuario.id)
        .order_by(TicketSoporte.creado_en)
        .all()
    )
    actividad = (
        db.query(Auditoria)
        .filter(Auditoria.usuario_id == usuario.id)
        .order_by(Auditoria.registrado_en.desc())
        .limit(LIMITE_REGISTRO_ACTIVIDAD)
        .all()
    )

    pedidos_publicos = [_pedido_publico(p) for p in pedidos]

    return {
        "generadoEn": _iso(utcnow()),
        "cuenta": {
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email,
            "rol": usuario.rol.codigo if usuario.rol else None,
            "estado": usuario.estado,
            "emailVerificado": usuario.email_verificado,
            "fechaRegistro": _iso(usuario.fecha_registro),
            "empresaActiva": usuario.organizacion.nombre if usuario.organizacion else None,
            "numeroIdentificacion": usuario.numero_identificacion,
            "cargo": usuario.cargo,
            "numeroResolucion": usuario.numero_resolucion,
            "resolucionVerificada": usuario.resolucion_verificada,
            "fotoUrl": usuario.foto_url,
            "perfilActualizadoEn": _iso(usuario.perfil_actualizado_en),
            "politicaVersionAceptada": usuario.politica_version,
            "politicaAceptadaEn": _iso(usuario.politica_aceptada_en),
        },
        "empresasCreadas": [
            {
                "nombre": e.nombre,
                "nit": e.nit,
                "sector": e.sector,
                "municipio": e.municipio,
                "telefono": e.telefono,
                "email": e.email,
                "activa": e.activa,
                "creadaEn": _iso(e.creado_en),
            }
            for e in empresas
        ],
        "compras": [
            {
                "bateria": c.bateria_nombre,
                "cantidad": c.cantidad,
                "tarifaUnitario": c.tarifa_unitario,
                "subtotal": c.subtotal,
                "iva": c.iva,
                "total": c.total,
                "estado": c.estado,
                "creadaEn": _iso(c.creado_en),
            }
            for c in compras
        ],
        "pedidosProductos": [
            {
                "numero": p["numero"],
                "subtotal": p["subtotal"],
                "iva": p["iva"],
                "total": p["total"],
                "estado": p["estado"],
                "creadoEn": p["creadoEn"],
                "items": [
                    {
                        "producto": i["nombre"],
                        "precioUnitario": i["precioUnitario"],
                        "cantidad": i["cantidad"],
                        "subtotal": i["subtotal"],
                    }
                    for i in p["items"]
                ],
            }
            for p in pedidos_publicos
        ],
        "mensajesSoporte": [
            {
                "mensaje": m.mensaje,
                "estado": m.estado,
                "creadoEn": _iso(m.creado_en),
                "respuesta": m.respuesta,
                "respondidoEn": _iso(m.respondido_en),
            }
            for m in mensajes
        ],
        "registroDeActividad": {
            "limiteDeEventos": LIMITE_REGISTRO_ACTIVIDAD,
            "eventos": [
                {"accion": a.accion, "entidad": a.entidad, "fecha": _iso(a.registrado_en), "ip": a.ip_origen}
                for a in actividad
            ],
        },
    }


def solicitar_eliminacion(db: Session, usuario: Usuario, motivo: str | None) -> dict:
    """Registra la solicitud como mensaje del Centro de ayuda; la atiende el Super Administrador."""
    if usuario.rol and usuario.rol.codigo == "SUPER_ADMINISTRADOR":
        raise AppError(403, "El Super Administrador no puede solicitar la eliminación de su cuenta desde la plataforma.")
    pendiente = (
        db.query(TicketSoporte)
        .filter(
            TicketSoporte.usuario_id == usuario.id,
            TicketSoporte.estado == "PENDIENTE",
            TicketSoporte.mensaje.startswith(PREFIJO_SOLICITUD_ELIMINACION),
        )
        .first()
    )
    if pendiente is not None:
        raise AppError(409, "Ya tienes una solicitud de eliminación pendiente. Te responderemos por el Centro de ayuda.")
    motivo = (motivo or "").strip()
    mensaje = f"{PREFIJO_SOLICITUD_ELIMINACION} Motivo: {motivo}" if motivo else PREFIJO_SOLICITUD_ELIMINACION
    return soporte_service.crear_ticket(db, usuario, mensaje)
