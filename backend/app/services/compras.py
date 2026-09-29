import uuid
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.models.commercial import Compra, Pago
from app.models.user import Usuario

TARIFA_POR_BATERIA = 10000.0
IVA_PORCENTAJE = 0.19


def _compra_publica(compra: Compra) -> dict:
    return {
        "id": str(compra.id),
        "usuarioId": str(compra.usuario_id),
        "organizacionId": str(compra.organizacion_id) if compra.organizacion_id else None,
        "bateriaNombre": compra.bateria_nombre,
        "cantidad": compra.cantidad,
        "tarifaUnitario": compra.tarifa_unitario,
        "subtotal": compra.subtotal,
        "iva": compra.iva,
        "total": compra.total,
        "estado": compra.estado,
        "fecha": compra.creado_en.isoformat(),
        "creadoEn": compra.creado_en.isoformat(),
    }


def _pago_publico(pago: Pago) -> dict:
    return {
        "id": str(pago.id),
        "compraId": str(pago.compra_id),
        "metodo": pago.metodo,
        "referencia": pago.referencia,
        "monto": pago.monto,
        "estado": pago.estado,
        "banco": pago.banco,
        "ultimosDigitos": pago.ultimos_digitos,
        "titular": pago.titular,
        "mensajeRespuesta": pago.mensaje_respuesta,
        "procesadoEn": pago.procesado_en.isoformat(),
    }


def crear_compra(db: Session, data, actual: Usuario) -> dict:
    cantidad = max(1, data.cantidad)
    subtotal = cantidad * TARIFA_POR_BATERIA
    iva = subtotal * IVA_PORCENTAJE
    total = subtotal + iva

    compra = Compra(
        usuario_id=actual.id,
        organizacion_id=data.organizacionId or actual.organizacion_id,
        bateria_nombre=data.bateriaNombre or "Batería de Riesgo Psicosocial",
        cantidad=cantidad,
        tarifa_unitario=TARIFA_POR_BATERIA,
        subtotal=subtotal,
        iva=iva,
        total=total,
        estado="PENDIENTE",
    )
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return _compra_publica(compra)


def listar_compras_usuario(db: Session, usuario_id: uuid.UUID, actual: Usuario) -> list[dict]:
    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and actual.id != usuario_id:
        raise AppError(403, "No tiene acceso a las compras de este usuario.")
    compras = (
        db.query(Compra)
        .filter(Compra.usuario_id == usuario_id)
        .order_by(Compra.creado_en.desc())
        .all()
    )
    return [_compra_publica(c) for c in compras]


def obtener_compra(db: Session, compra_id: uuid.UUID, actual: Usuario) -> dict:
    compra = db.query(Compra).options(joinedload(Compra.pagos)).filter(Compra.id == compra_id).first()
    if compra is None:
        raise AppError(404, "Compra no encontrada.")
    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and actual.id != compra.usuario_id:
        raise AppError(403, "No tiene acceso a esta compra.")
    res = _compra_publica(compra)
    res["pagos"] = [_pago_publico(p) for p in compra.pagos]
    return res


def procesar_pago(db: Session, data, actual: Usuario) -> dict:
    """Servicio simulador de pasarela de pago real en el backend.

    Nota de prototipo: Este servicio simula la interacción con una pasarela de pagos colombiana (PSE/Tarjeta).
    Registra de forma real la transacción en la tabla 'pagos' de PostgreSQL, asocia la transacción
    a la 'Compra', y actualiza el estado de la compra a 'PAGADA' si la transacción es aprobada.
    """
    compra = db.query(Compra).filter(Compra.id == data.compraId).first()
    if compra is None:
        raise AppError(404, "Compra no encontrada.")

    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and actual.id != compra.usuario_id:
        raise AppError(403, "No tiene acceso a esta compra.")

    if compra.estado == "PAGADA":
        raise AppError(400, "Esta compra ya ha sido pagada previamente.")

    if data.monto is not None and round(data.monto, 2) != round(compra.total, 2):
        raise AppError(400, "El monto del pago no coincide con el total de la compra.")

    metodo = (data.metodo or "tarjeta").lower()
    prefix = "PAY-PSE" if metodo == "pse" else "PAY-CARD"
    referencia = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    aprobado = True
    mensaje = "Pago aprobado exitosamente por la pasarela de pagos (Simulador PSE/Tarjeta)."
    if data.cvv == "000" or (data.monto and data.monto == 999.0):
        aprobado = False
        mensaje = "Pago rechazado: transacción declinada por la entidad financiera."

    estado_pago = "APROBADO" if aprobado else "RECHAZADO"

    ultimos_digitos = None
    if data.numeroTarjeta:
        num_limpio = data.numeroTarjeta.replace(" ", "")
        if len(num_limpio) >= 4:
            ultimos_digitos = num_limpio[-4:]

    try:
        pago = Pago(
            compra_id=compra.id,
            metodo=metodo,
            referencia=referencia,
            monto=data.monto or compra.total,
            estado=estado_pago,
            banco=data.banco,
            ultimos_digitos=ultimos_digitos,
            titular=data.nombreTarjeta,
            mensaje_respuesta=mensaje,
        )
        db.add(pago)

        if aprobado:
            compra.estado = "PAGADA"

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(pago)

    res = _pago_publico(pago)
    res["compraEstado"] = compra.estado
    return res
