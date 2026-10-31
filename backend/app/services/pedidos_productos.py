import logging
import uuid
from datetime import timedelta

from sqlalchemy.orm import Session, joinedload

from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.product import Producto
from app.models.product_order import PagoPedidoProducto, PedidoProducto, PedidoProductoItem
from app.models.user import Usuario
from app.services import wompi as wompi_service
from app.services.productos import _alertar_stock_bajo, maneja_stock
from app.services.notificaciones import notificar


logger = logging.getLogger(__name__)

IVA_PORCENTAJE = 0.19
TIEMPO_EXPIRACION_PEDIDO_MINUTOS = 30
ESTADOS_FINALES_WOMPI = {"APPROVED", "DECLINED", "VOIDED", "ERROR"}
VALOR_MAXIMO_PEDIDO = 1_000_000_000


def _pedido_publico(pedido: PedidoProducto, incluir_pagos: bool = False) -> dict:
    resultado = {
        "id": str(pedido.id),
        "numero": f"PED-{pedido.id.hex[:10].upper()}",
        "usuarioId": str(pedido.usuario_id),
        "subtotal": pedido.subtotal,
        "iva": pedido.iva,
        "total": pedido.total,
        "estado": pedido.estado,
        "fecha": pedido.creado_en.isoformat(),
        "creadoEn": pedido.creado_en.isoformat(),
        "items": [
            {
                "id": str(item.id),
                "productoId": str(item.producto_id) if item.producto_id else None,
                "nombre": item.nombre_producto,
                "precioUnitario": item.precio_unitario,
                "cantidad": item.cantidad,
                "subtotal": item.subtotal,
            }
            for item in pedido.items
        ],
    }

    if incluir_pagos:
        resultado["pagos"] = [_pago_publico(pago) for pago in pedido.pagos]

    return resultado


def _pago_publico(pago: PagoPedidoProducto) -> dict:
    return {
        "id": str(pago.id),
        "pedidoId": str(pago.pedido_id),
        "metodo": pago.metodo,
        "referencia": pago.referencia,
        "monto": pago.monto,
        "estado": pago.estado,
        "wompiTransactionId": pago.wompi_transaction_id,
        "wompiStatus": pago.wompi_status,
        "mensajeRespuesta": pago.mensaje_respuesta,
        "procesadoEn": pago.procesado_en.isoformat(),
    }


def _obtener_pedido(db: Session, pedido_id, actual: Usuario) -> PedidoProducto:
    pedido = (
        db.query(PedidoProducto)
        .options(
            joinedload(PedidoProducto.items),
            joinedload(PedidoProducto.pagos),
        )
        .filter(PedidoProducto.id == pedido_id)
        .first()
    )

    if pedido is None:
        raise AppError(404, "Pedido no encontrado.")

    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and actual.id != pedido.usuario_id:
        raise AppError(403, "No tiene acceso a este pedido.")

    return pedido


def _expirar_pedidos_vencidos(db: Session, usuario_id=None) -> None:
    limite = utcnow() - timedelta(minutes=TIEMPO_EXPIRACION_PEDIDO_MINUTOS)

    query = db.query(PedidoProducto).filter(
        PedidoProducto.estado == "PENDIENTE",
        PedidoProducto.creado_en <= limite,
    )
    if usuario_id is not None:
        query = query.filter(PedidoProducto.usuario_id == usuario_id)

    pedidos = query.all()
    for pedido in pedidos:
        _reconciliar_pagos_pendientes(db, pedido)
        if pedido.estado == "PENDIENTE" and not _tiene_pago_en_curso(db, pedido):
            pedido.estado = "EXPIRADA"
            _reintegrar_stock(db, pedido)
            db.commit()

    if pedidos:
        db.commit()


def _tiene_pago_en_curso(db: Session, pedido: PedidoProducto) -> bool:
    return (
        db.query(PagoPedidoProducto.id)
        .filter(
            PagoPedidoProducto.pedido_id == pedido.id,
            PagoPedidoProducto.wompi_transaction_id.isnot(None),
            PagoPedidoProducto.wompi_status == "PENDING",
        )
        .first()
        is not None
    )


def _reconciliar_pagos_pendientes(db: Session, pedido: PedidoProducto) -> None:
    pagos = (
        db.query(PagoPedidoProducto)
        .filter(
            PagoPedidoProducto.pedido_id == pedido.id,
            PagoPedidoProducto.wompi_transaction_id.isnot(None),
        )
        .all()
    )

    for pago in pagos:
        if (pago.wompi_status or "").upper() in ESTADOS_FINALES_WOMPI:
            continue

        try:
            respuesta = wompi_service.consultar_transaccion(pago.wompi_transaction_id)
            transaction = respuesta.get("data")
            if isinstance(transaction, dict):
                procesar_evento_wompi(db, transaction)
        except (RuntimeError, ValueError, AppError) as exc:
            db.rollback()
            logger.warning(
                "No se pudo reconciliar el pedido de productos %s con Wompi: %s",
                pedido.id,
                exc,
            )

    db.refresh(pedido)


def _reintegrar_stock(db: Session, pedido: PedidoProducto) -> None:
    """Devuelve al inventario las unidades reservadas, una sola vez por pedido."""
    if pedido.stock_reintegrado:
        return
    for item in pedido.items:
        if item.producto_id is None:
            continue
        producto = db.query(Producto).filter(Producto.id == item.producto_id).with_for_update().first()
        if producto is not None and maneja_stock(producto):
            producto.stock += item.cantidad
    pedido.stock_reintegrado = True


def crear_pedido(db: Session, data, actual: Usuario) -> dict:
    _expirar_pedidos_vencidos(db, usuario_id=actual.id)

    cantidades = {}
    for item in data.items:
        cantidades[item.producto_id] = cantidades.get(item.producto_id, 0) + item.cantidad

    if any(cantidad > 99 for cantidad in cantidades.values()):
        raise AppError(400, "La cantidad máxima por producto es 99.")

    productos = (
        db.query(Producto)
        .filter(
            Producto.id.in_(list(cantidades.keys())),
            Producto.activo.is_(True),
        )
        .with_for_update()
        .all()
    )
    productos_por_id = {producto.id: producto for producto in productos}

    faltantes = [str(pid) for pid in cantidades if pid not in productos_por_id]
    if faltantes:
        raise AppError(404, "Uno o más productos ya no están disponibles.")

    subtotal = 0
    lineas = []

    for producto_id, cantidad in cantidades.items():
        producto = productos_por_id[producto_id]
        if maneja_stock(producto) and producto.stock < cantidad:
            raise AppError(409, f"Stock insuficiente para {producto.nombre}. Disponibles: {producto.stock}.")
        linea_subtotal = producto.precio * cantidad
        subtotal += linea_subtotal
        lineas.append(
            PedidoProductoItem(
                producto_id=producto.id,
                nombre_producto=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=cantidad,
                subtotal=linea_subtotal,
            )
        )

    iva = int(round(subtotal * IVA_PORCENTAJE))
    total = subtotal + iva

    if total > VALOR_MAXIMO_PEDIDO:
        raise AppError(400, "El valor del pedido supera el máximo permitido.")

    for producto_id, cantidad in cantidades.items():
        producto = productos_por_id[producto_id]
        if not maneja_stock(producto):
            continue
        stock_anterior = producto.stock
        producto.stock -= cantidad
        if stock_anterior > 5 and producto.stock <= 5:
            _alertar_stock_bajo(db, producto)

    pedido = PedidoProducto(
        usuario_id=actual.id,
        subtotal=subtotal,
        iva=iva,
        total=total,
        estado="PENDIENTE",
    )
    pedido.items = lineas

    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    return _pedido_publico(pedido, incluir_pagos=True)


def listar_pedidos_usuario(db: Session, usuario_id, actual: Usuario) -> list[dict]:
    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and actual.id != usuario_id:
        raise AppError(403, "No tiene acceso a los pedidos de este usuario.")

    _expirar_pedidos_vencidos(db, usuario_id=usuario_id)

    pedidos = (
        db.query(PedidoProducto)
        .options(joinedload(PedidoProducto.items))
        .filter(PedidoProducto.usuario_id == usuario_id)
        .order_by(PedidoProducto.creado_en.desc())
        .all()
    )
    return [_pedido_publico(pedido) for pedido in pedidos]


def obtener_pedido(db: Session, pedido_id, actual: Usuario) -> dict:
    pedido = _obtener_pedido(db, pedido_id, actual)

    if pedido.estado in {"PENDIENTE", "EXPIRADA"}:
        _reconciliar_pagos_pendientes(db, pedido)

    if pedido.estado == "PENDIENTE":
        limite = pedido.creado_en + timedelta(minutes=TIEMPO_EXPIRACION_PEDIDO_MINUTOS)
        if utcnow() >= limite and not _tiene_pago_en_curso(db, pedido):
            pedido.estado = "EXPIRADA"
            _reintegrar_stock(db, pedido)
            db.commit()
            db.refresh(pedido)

    return _pedido_publico(pedido, incluir_pagos=True)


def preparar_checkout_wompi(db: Session, pedido_id, actual: Usuario) -> dict:
    pedido = _obtener_pedido(db, pedido_id, actual)

    if pedido.estado == "PENDIENTE":
        _reconciliar_pagos_pendientes(db, pedido)

    if pedido.estado == "PENDIENTE" and _tiene_pago_en_curso(db, pedido):
        raise AppError(400, "Este pedido tiene un pago en proceso. Espera la confirmación de Wompi.")

    if pedido.estado == "PAGADA":
        raise AppError(400, "Este pedido ya fue pagado.")
    if pedido.estado in {"EXPIRADA", "CANCELADA"}:
        raise AppError(400, "Este pedido ya no puede continuar con el pago.")

    public_key = wompi_service.get_wompi_public_key()
    if not public_key:
        raise AppError(503, "La llave pública de Wompi no está configurada.")

    amount_in_cents = pedido.total * 100
    referencia = f"MPROD-{pedido.id.hex[:12].upper()}-{uuid.uuid4().hex[:12].upper()}"

    try:
        firma = wompi_service.generate_integrity_signature(
            reference=referencia,
            amount_in_cents=amount_in_cents,
            currency="COP",
        )
    except RuntimeError as exc:
        raise AppError(503, str(exc)) from exc

    pago = PagoPedidoProducto(
        pedido_id=pedido.id,
        metodo="wompi",
        referencia=referencia,
        monto=pedido.total,
        estado="PENDIENTE",
        wompi_status="PENDING",
        mensaje_respuesta="Checkout Wompi preparado. Pendiente de completar el pago.",
    )

    try:
        db.add(pago)
        db.commit()
        db.refresh(pago)
    except Exception:
        db.rollback()
        raise

    return {
        "pedidoId": str(pedido.id),
        "pagoId": str(pago.id),
        "reference": referencia,
        "currency": "COP",
        "amountInCents": amount_in_cents,
        "publicKey": public_key,
        "signature": firma,
        "total": pedido.total,
    }


def procesar_pago(db: Session, data, actual: Usuario) -> dict:
    pedido = _obtener_pedido(db, data.pedido_id, actual)

    try:
        transaccion = wompi_service.consultar_transaccion(data.wompi_transaction_id.strip())
    except (RuntimeError, ValueError) as exc:
        raise AppError(503, str(exc)) from exc

    transaction = transaccion.get("data")
    if not isinstance(transaction, dict):
        raise AppError(502, "Wompi no devolvió una transacción válida.")

    reference = transaction.get("reference")
    payment = (
        db.query(PagoPedidoProducto)
        .filter(
            PagoPedidoProducto.pedido_id == pedido.id,
            PagoPedidoProducto.referencia == reference,
        )
        .first()
    )

    if payment is None:
        raise AppError(400, "La referencia de la transacción no corresponde a este pedido.")

    if transaction.get("currency") != "COP":
        raise AppError(400, "La moneda confirmada por Wompi no es válida.")

    if transaction.get("amount_in_cents") != pedido.total * 100:
        raise AppError(400, "El monto confirmado por Wompi no coincide con el total del pedido.")

    return procesar_evento_wompi(db, transaction)


def procesar_evento_wompi(db: Session, transaction: dict) -> dict:
    transaction_id = transaction.get("id")
    status = str(transaction.get("status", "")).upper()
    reference = transaction.get("reference")
    amount_in_cents = transaction.get("amount_in_cents")
    currency = transaction.get("currency")

    if not isinstance(transaction_id, str) or not transaction_id.strip():
        raise AppError(400, "La transacción de Wompi no tiene identificador.")
    if not isinstance(reference, str) or not reference.strip():
        raise AppError(400, "La transacción de Wompi no tiene referencia.")
    if not isinstance(amount_in_cents, int) or isinstance(amount_in_cents, bool):
        raise AppError(400, "La transacción de Wompi no tiene un monto válido.")
    if currency != "COP":
        raise AppError(400, "La moneda recibida en el webhook no es válida.")

    pago = (
        db.query(PagoPedidoProducto)
        .filter(
            PagoPedidoProducto.referencia == reference,
            PagoPedidoProducto.metodo == "wompi",
        )
        .first()
    )
    if pago is None:
        raise AppError(404, "No se encontró un pago asociado a la referencia de Wompi.")

    pedido = db.query(PedidoProducto).filter(PedidoProducto.id == pago.pedido_id).with_for_update().first()
    if pedido is None:
        raise AppError(404, "No se encontró el pedido asociado al pago.")

    if amount_in_cents != pedido.total * 100:
        raise AppError(400, "El monto recibido de Wompi no coincide con el pedido.")

    otro_pago = (
        db.query(PagoPedidoProducto)
        .filter(PagoPedidoProducto.wompi_transaction_id == transaction_id)
        .first()
    )
    if otro_pago is not None and otro_pago.id != pago.id:
        raise AppError(409, "La transacción de Wompi ya está asociada a otro pago.")

    estado_previo = (pago.wompi_status or "").upper()
    if estado_previo in ESTADOS_FINALES_WOMPI and status != estado_previo:
        return {
            "ok": True,
            "transactionId": transaction_id,
            "estado": estado_previo,
            "pagoId": str(pago.id),
            "pedidoId": str(pedido.id),
            "pedidoEstado": pedido.estado,
        }

    pago.wompi_transaction_id = transaction_id
    pago.wompi_status = status
    pago.wompi_payment_method = transaction.get("payment_method_type")

    if status == "APPROVED":
        pago.estado = "APROBADO"
        pago.mensaje_respuesta = "Pago aprobado y confirmado por Wompi."
        ya_pagado = pedido.estado == "PAGADA"
        pedido.estado = "PAGADA"

        if not ya_pagado:
            notificar(
                db,
                usuario_id=pedido.usuario_id,
                tipo="COMPRA_APROBADA",
                titulo="Compra de productos aprobada",
                mensaje=f"Tu pedido PED-{pedido.id.hex[:10].upper()} fue pagado correctamente.",
                commit=False,
            )
    elif status == "DECLINED":
        pago.estado = "RECHAZADO"
        pago.mensaje_respuesta = "El pago fue rechazado por Wompi."
        pedido.estado = "RECHAZADO"
    elif status == "VOIDED":
        pago.estado = "ANULADO"
        pago.mensaje_respuesta = "El pago fue anulado por Wompi."
        pedido.estado = "PENDIENTE"
    elif status == "ERROR":
        pago.estado = "ERROR"
        pago.mensaje_respuesta = "Wompi reportó un error al procesar el pago."
        pedido.estado = "ERROR"
    elif status == "PENDING":
        pago.estado = "PENDIENTE"
        pago.mensaje_respuesta = "El pago se encuentra pendiente de confirmación por Wompi."
        pedido.estado = "PENDIENTE"
    else:
        pago.estado = status or "ERROR"
        pago.mensaje_respuesta = "Wompi devolvió un estado no reconocido."
        pedido.estado = "ERROR"

    db.commit()
    db.refresh(pago)
    db.refresh(pedido)

    return {
        "ok": True,
        "transactionId": transaction_id,
        "estado": status,
        "pagoId": str(pago.id),
        "pedidoId": str(pedido.id),
        "pedidoEstado": pedido.estado,
    }


def actualizar_estado_envio(db: Session, pedido_id, estado: str, actual: Usuario) -> dict:
    estados_permitidos = {"ENVIADO", "ENTREGADO"}
    estado = (estado or "").strip().upper()
    if estado not in estados_permitidos:
        raise AppError(400, "Estado no válido para seguimiento del pedido.")
    pedido = _obtener_pedido(db, pedido_id, actual)
    if estado in {"ENVIADO", "ENTREGADO"} and pedido.estado not in {"PAGADA", "ENVIADO", "ENTREGADO"}:
        raise AppError(400, "Solo se puede enviar un pedido que ya fue pagado.")
    anterior = pedido.estado
    pedido.estado = estado
    notificar(
        db, usuario_id=pedido.usuario_id, tipo="ESTADO_PEDIDO_PRODUCTOS",
        titulo="Actualización de tu pedido",
        mensaje=f"El pedido PED-{pedido.id.hex[:10].upper()} cambió de {anterior} a {estado}.",
        commit=False,
    )
    db.commit()
    db.refresh(pedido)
    return _pedido_publico(pedido, incluir_pagos=True)


def cancelar_pedido(db: Session, pedido_id, actual: Usuario) -> dict:
    pedido = _obtener_pedido(db, pedido_id, actual)

    if pedido.estado != "PENDIENTE":
        raise AppError(400, "Este pedido no puede cancelarse en su estado actual.")

    _reconciliar_pagos_pendientes(db, pedido)

    if pedido.estado == "PENDIENTE" and _tiene_pago_en_curso(db, pedido):
        raise AppError(400, "Este pedido tiene un pago en proceso. Espera la confirmación de Wompi.")

    if pedido.estado != "PENDIENTE":
        raise AppError(400, "Este pedido no puede cancelarse en su estado actual.")

    pedido.estado = "CANCELADA"
    _reintegrar_stock(db, pedido)
    db.commit()
    db.refresh(pedido)
    return _pedido_publico(pedido, incluir_pagos=True)
