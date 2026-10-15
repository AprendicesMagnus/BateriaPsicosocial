import logging
import uuid
from datetime import timedelta

from sqlalchemy.orm import Session, joinedload

from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.commercial import Compra, Pago
from app.models.plan import PlanBateria
from app.models.user import Usuario
from app.services import wompi as wompi_service


logger = logging.getLogger(__name__)

TARIFA_POR_BATERIA = 10000.0
IVA_PORCENTAJE = 0.19
TIEMPO_EXPIRACION_COMPRA_MINUTOS = 30

# Estados de Wompi que ya no cambian.
ESTADOS_FINALES_WOMPI = {"APPROVED", "DECLINED", "VOIDED", "ERROR"}


def _compra_publica(compra: Compra) -> dict:
    return {
        "id": str(compra.id),
        "usuarioId": str(compra.usuario_id),
        "organizacionId": (
            str(compra.organizacion_id)
            if compra.organizacion_id
            else None
        ),
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


def _tiene_pago_en_curso(
    db: Session,
    compra: Compra,
) -> bool:
    """
    Indica si la compra tiene una transacción de Wompi ya creada
    (con transaction id) que todavía no tiene un estado final.

    El pago del checkout nace con wompi_status="PENDING" pero SIN
    transaction id: eso significa que el usuario aún no ha pagado
    (o abandonó el widget) y no cuenta como "en curso".
    """

    return (
        db.query(Pago.id)
        .filter(
            Pago.compra_id == compra.id,
            Pago.metodo == "wompi",
            Pago.wompi_transaction_id.isnot(None),
            Pago.wompi_status == "PENDING",
        )
        .first()
        is not None
    )


def _reconciliar_pago_pendiente(
    db: Session,
    compra: Compra,
) -> None:
    """
    Consulta directamente en Wompi las transacciones de la compra
    cuyo ID ya se conoce pero que todavía no tienen estado final, y
    aplica el resultado con la misma lógica del webhook.

    Cubre el caso en que el usuario cerró sesión o la pestaña
    antes de que el frontend confirmara el pago y el webhook
    no llegó o llegó tarde.

    Nunca lanza excepciones: si Wompi no responde, la compra
    conserva su estado y se reintentará en la próxima consulta.
    """

    pagos = (
        db.query(Pago)
        .filter(
            Pago.compra_id == compra.id,
            Pago.metodo == "wompi",
            Pago.wompi_transaction_id.isnot(None),
        )
        .all()
    )

    pendientes = [
        pago.wompi_transaction_id
        for pago in pagos
        if (pago.wompi_status or "").upper()
        not in ESTADOS_FINALES_WOMPI
    ]

    for transaction_id in pendientes:
        try:
            respuesta = wompi_service.consultar_transaccion(
                transaction_id
            )

            transaccion = respuesta.get("data")

            if isinstance(transaccion, dict):
                procesar_evento_wompi(
                    db=db,
                    transaction=transaccion,
                )

        except (RuntimeError, ValueError, AppError) as exc:
            db.rollback()

            logger.warning(
                "No se pudo reconciliar la transacción %s "
                "de Wompi: %s",
                transaction_id,
                exc,
            )

    if pendientes:
        db.refresh(compra)


def _expirar_compras_vencidas(
    db: Session,
    usuario_id: uuid.UUID | None = None,
) -> None:
    """
    Marca como EXPIRADA cualquier compra PENDIENTE
    que haya superado los 30 minutos desde su creación.
    """

    limite = (
        utcnow()
        - timedelta(
            minutes=TIEMPO_EXPIRACION_COMPRA_MINUTOS
        )
    )

    query = (
        db.query(Compra)
        .filter(
            Compra.estado == "PENDIENTE",
            Compra.creado_en <= limite,
        )
    )

    if usuario_id is not None:
        query = query.filter(
            Compra.usuario_id == usuario_id
        )

    compras_vencidas = query.all()

    if not compras_vencidas:
        return

    for compra in compras_vencidas:
        # Antes de expirar, confirmar con Wompi si el usuario
        # alcanzó a pagar (o tiene un pago aún en proceso).
        _reconciliar_pago_pendiente(db, compra)

        if (
            compra.estado == "PENDIENTE"
            and not _tiene_pago_en_curso(db, compra)
        ):
            compra.estado = "EXPIRADA"

            # Se guarda de inmediato para que un fallo posterior de
            # Wompi (que hace rollback) no deshaga esta expiración.
            db.commit()

    db.commit()


def _calcular_subtotal(db: Session, cantidad: int, plan_id) -> float:
    """Subtotal antes de IVA. Con plan elegido es el PRECIO FIJO del plan (no se multiplica por la
    cantidad); la cantidad solo debe caber en el rango del plan. Sin plan: cantidad x tarifa por defecto."""
    if not plan_id:
        return cantidad * TARIFA_POR_BATERIA
    plan = db.query(PlanBateria).filter(PlanBateria.id == plan_id, PlanBateria.activo.is_(True)).first()
    if plan is None:
        raise AppError(404, "El plan seleccionado ya no está disponible. Elige otro.")
    if cantidad < plan.cantidad_min or (plan.cantidad_max is not None and cantidad > plan.cantidad_max):
        raise AppError(400, "La cantidad no corresponde al plan seleccionado.")
    return float(plan.precio_unitario)


def crear_compra(
    db: Session,
    data,
    actual: Usuario,
) -> dict:
    """
    Crea una nueva compra.

    Reglas:

    - Una compra PENDIENTE tiene una vigencia de 30 minutos.
    - Una compra PENDIENTE vigente bloquea una nueva compra
      de la misma batería para el mismo usuario y organización.
    - Una compra EXPIRADA no bloquea nuevas compras.
    - Las compras RECHAZADO, ANULADO, ERROR y CANCELADA
      permanecen en el historial y no bloquean nuevas compras.
    """

    _expirar_compras_vencidas(
        db,
        usuario_id=actual.id,
    )

    cantidad = max(1, data.cantidad)

    organizacion_id = (
        data.organizacionId
        or actual.organizacion_id
    )

    bateria_nombre = (
        data.bateriaNombre
        or "Batería de Riesgo Psicosocial"
    ).strip()

    # ==================================================
    # EVITAR COMPRAS PENDIENTES DUPLICADAS
    # ==================================================

    compra_pendiente = (
        db.query(Compra)
        .filter(
            Compra.usuario_id == actual.id,
            Compra.organizacion_id == organizacion_id,
            Compra.bateria_nombre == bateria_nombre,
            Compra.estado == "PENDIENTE",
        )
        .order_by(
            Compra.creado_en.desc()
        )
        .first()
    )

    if compra_pendiente is not None:
        raise AppError(
            409,
            (
                "Ya existe una compra pendiente "
                "para esta batería. Puede continuar "
                "el pago desde esa compra o cancelarla."
            ),
            compraId=str(compra_pendiente.id),
            estado=compra_pendiente.estado,
        )

    # ==================================================
    # CALCULAR VALORES
    # ==================================================

    subtotal = _calcular_subtotal(db, cantidad, getattr(data, "planId", None))
    tarifa = subtotal / cantidad  # tarifa efectiva por batería (informativa)
    iva = subtotal * IVA_PORCENTAJE
    total = subtotal + iva

    # ==================================================
    # CREAR COMPRA
    # ==================================================

    compra = Compra(
        usuario_id=actual.id,
        organizacion_id=organizacion_id,
        bateria_nombre=bateria_nombre,
        cantidad=cantidad,
        tarifa_unitario=tarifa,
        subtotal=subtotal,
        iva=iva,
        total=total,
        estado="PENDIENTE",
    )

    db.add(compra)
    db.commit()
    db.refresh(compra)

    return _compra_publica(compra)


def listar_compras_usuario(
    db: Session,
    usuario_id: uuid.UUID,
    actual: Usuario,
) -> list[dict]:

    if (
        actual.rol.codigo != "SUPER_ADMINISTRADOR"
        and actual.id != usuario_id
    ):
        raise AppError(
            403,
            "No tiene acceso a las compras de este usuario.",
        )

    # Actualizar automáticamente las compras PENDIENTES
    # que ya hayan superado los 30 minutos.
    _expirar_compras_vencidas(
        db,
        usuario_id=usuario_id,
    )

    compras = (
        db.query(Compra)
        .filter(
            Compra.usuario_id == usuario_id,
        )
        .order_by(
            Compra.creado_en.desc()
        )
        .all()
    )

    return [
        _compra_publica(compra)
        for compra in compras
    ]


def obtener_compra(
    db: Session,
    compra_id: uuid.UUID,
    actual: Usuario,
) -> dict:

    compra = (
        db.query(Compra)
        .options(
            joinedload(Compra.pagos)
        )
        .filter(
            Compra.id == compra_id
        )
        .first()
    )

    if compra is None:
        raise AppError(
            404,
            "Compra no encontrada.",
        )

    if (
        actual.rol.codigo != "SUPER_ADMINISTRADOR"
        and actual.id != compra.usuario_id
    ):
        raise AppError(
            403,
            "No tiene acceso a esta compra.",
        )

    # ==================================================
    # RECONCILIAR CON WOMPI
    # ==================================================
    #
    # Si el usuario pagó pero el frontend no pudo confirmarlo
    # (sesión cerrada, pestaña cerrada) y el webhook aún no
    # llegó, se consulta a Wompi antes de responder o expirar.

    if compra.estado in ("PENDIENTE", "EXPIRADA"):
        _reconciliar_pago_pendiente(db, compra)

    # ==================================================
    # VERIFICAR EXPIRACIÓN
    # ==================================================

    if compra.estado == "PENDIENTE":
        limite = (
            compra.creado_en
            + timedelta(
                minutes=TIEMPO_EXPIRACION_COMPRA_MINUTOS
            )
        )

        if (
            utcnow() >= limite
            and not _tiene_pago_en_curso(db, compra)
        ):
            compra.estado = "EXPIRADA"
            db.commit()
            db.refresh(compra)

    res = _compra_publica(compra)

    res["pagos"] = [
        _pago_publico(pago)
        for pago in compra.pagos
    ]

    return res


def procesar_pago(
    db: Session,
    data,
    actual: Usuario,
) -> dict:
    """
    Registra y valida el resultado de una transacción
    procesada por Wompi.

    La transacción se consulta directamente en Wompi
    y el estado del pago y de la compra se actualiza
    según el resultado real de Wompi.
    """

    compra = (
        db.query(Compra)
        .filter(
            Compra.id == data.compraId
        )
        .first()
    )

    if compra is None:
        raise AppError(
            404,
            "Compra no encontrada.",
        )

    # ==================================================
    # VALIDAR PROPIETARIO DE LA COMPRA
    # ==================================================

    if (
        actual.rol.codigo != "SUPER_ADMINISTRADOR"
        and actual.id != compra.usuario_id
    ):
        raise AppError(
            403,
            "No tiene acceso a esta compra.",
        )

    # ==================================================
    # VALIDAR TRANSACTION ID
    # ==================================================

    if not data.wompiTransactionId:
        raise AppError(
            400,
            "La transacción de Wompi es obligatoria.",
        )

    transaction_id = (
        data.wompiTransactionId.strip()
    )

    # ==================================================
    # CONSULTAR TRANSACCIÓN DIRECTAMENTE EN WOMPI
    # ==================================================

    transaccion = (
        wompi_service.consultar_transaccion(
            transaction_id
        )
    )

    datos_transaccion = transaccion.get(
        "data",
        {},
    )

    estado_wompi = (
        datos_transaccion
        .get("status", "")
        .upper()
    )

    # ==================================================
    # VERIFICAR EXPIRACIÓN
    # ==================================================
    #
    # La expiración solo se aplica si Wompi no tiene una
    # transacción aprobada o en proceso para esta compra:
    # un pago real nunca debe perderse por haber tardado
    # más de 30 minutos en confirmarse.

    if (
        compra.estado == "PENDIENTE"
        and estado_wompi not in ("APPROVED", "PENDING")
    ):
        limite = (
            compra.creado_en
            + timedelta(
                minutes=TIEMPO_EXPIRACION_COMPRA_MINUTOS
            )
        )

        if utcnow() >= limite:
            compra.estado = "EXPIRADA"
            db.commit()

            raise AppError(
                400,
                (
                    "Esta compra ha expirado. "
                    "Debe crear una nueva compra para "
                    "realizar el pago."
                ),
                compraId=str(compra.id),
                estado=compra.estado,
            )

    # ==================================================
    # BUSCAR EL PAGO DEL CHECKOUT
    # ==================================================

    pago = (
        db.query(Pago)
        .filter(
            Pago.compra_id == compra.id,
            Pago.metodo == "wompi",
            Pago.wompi_transaction_id.is_(None),
        )
        .order_by(
            Pago.procesado_en.desc()
        )
        .first()
    )

    # ==================================================
    # SI NO ENCONTRAMOS PAGO PENDIENTE, BUSCAR
    # SI LA TRANSACCIÓN YA FUE PROCESADA
    # ==================================================

    if pago is None:
        pago_existente = (
            db.query(Pago)
            .filter(
                Pago.wompi_transaction_id
                == transaction_id
            )
            .first()
        )

        if pago_existente is not None:
            compra_existente = (
                db.query(Compra)
                .filter(
                    Compra.id
                    == pago_existente.compra_id
                )
                .first()
            )

            res = _pago_publico(
                pago_existente
            )

            res["compraEstado"] = (
                compra_existente.estado
                if compra_existente is not None
                else None
            )

            return res

        raise AppError(
            404,
            (
                "No se encontró un intento de pago "
                "asociado a esta compra."
            ),
        )

    # ==================================================
    # VALIDAR REFERENCIA
    # ==================================================

    referencia_wompi = (
        datos_transaccion.get(
            "reference"
        )
    )

    if not referencia_wompi:
        raise AppError(
            400,
            "La transacción de Wompi no tiene referencia.",
        )

    referencia_wompi = (
        referencia_wompi.strip()
    )

    if referencia_wompi != pago.referencia:
        raise AppError(
            400,
            (
                "La referencia de la transacción "
                "no coincide con la referencia del "
                "pago generado por MagnusSIG."
            ),
        )

    # ==================================================
    # VALIDAR MONTO
    # ==================================================

    monto_wompi_centavos = (
        datos_transaccion.get(
            "amount_in_cents"
        )
    )

    if monto_wompi_centavos is None:
        raise AppError(
            400,
            "La transacción de Wompi no tiene monto.",
        )

    monto_esperado_centavos = int(
        round(compra.total * 100)
    )

    if (
        monto_wompi_centavos
        != monto_esperado_centavos
    ):
        raise AppError(
            400,
            (
                "El monto confirmado por Wompi "
                "no coincide con el total de la compra."
            ),
        )

    # ==================================================
    # VALIDAR MONEDA
    # ==================================================

    moneda_wompi = (
        datos_transaccion.get(
            "currency"
        )
    )

    if moneda_wompi != "COP":
        raise AppError(
            400,
            (
                "La moneda confirmada por Wompi "
                "no es válida para esta compra."
            ),
        )

    # ==================================================
    # EVITAR DUPLICAR UNA TRANSACCIÓN
    # ==================================================

    pago_existente = (
        db.query(Pago)
        .filter(
            Pago.wompi_transaction_id
            == transaction_id
        )
        .first()
    )

    if (
        pago_existente is not None
        and pago_existente.id != pago.id
    ):
        raise AppError(
            409,
            (
                "La transacción de Wompi ya está "
                "asociada a otro pago."
            ),
        )

    # ==================================================
    # ACTUALIZAR INFORMACIÓN DEL PAGO
    # ==================================================

    pago.wompi_transaction_id = (
        transaction_id
    )

    pago.wompi_status = (
        estado_wompi
    )

    pago.wompi_payment_method = (
        data.wompiPaymentMethod
        or datos_transaccion.get(
            "payment_method_type"
        )
    )

    pago.banco = (
        data.banco
        or datos_transaccion.get(
            "bank"
        )
    )

    pago.monto = compra.total

    # ==================================================
    # ACTUALIZAR SEGÚN EL ESTADO REAL DE WOMPI
    # ==================================================

    if estado_wompi == "APPROVED":
        pago.estado = "APROBADO"

        pago.mensaje_respuesta = (
            "Pago aprobado y validado con Wompi."
        )

        compra.estado = "PAGADA"

    elif estado_wompi == "DECLINED":
        pago.estado = "RECHAZADO"

        pago.mensaje_respuesta = (
            "El pago fue rechazado por Wompi."
        )

        compra.estado = "RECHAZADO"

    elif estado_wompi == "VOIDED":
        pago.estado = "ANULADO"

        pago.mensaje_respuesta = (
            "El pago fue anulado por Wompi."
        )

        compra.estado = "PENDIENTE"

    elif estado_wompi == "ERROR":
        pago.estado = "ERROR"

        pago.mensaje_respuesta = (
            "Wompi reportó un error al procesar el pago."
        )

        compra.estado = "ERROR"

    elif estado_wompi == "PENDING":
        pago.estado = "PENDIENTE"

        pago.mensaje_respuesta = (
            "El pago se encuentra pendiente de "
            "confirmación por Wompi."
        )

        compra.estado = "PENDIENTE"

    else:
        pago.estado = estado_wompi or "ERROR"

        pago.mensaje_respuesta = (
            "Wompi devolvió un estado no reconocido."
        )

        compra.estado = "ERROR"

    # ==================================================
    # GUARDAR TODO EN UNA SOLA TRANSACCIÓN
    # ==================================================

    try:
        db.commit()

        db.refresh(pago)
        db.refresh(compra)

    except Exception:
        db.rollback()
        raise

    # ==================================================
    # RESPUESTA
    # ==================================================

    res = _pago_publico(pago)

    res["compraEstado"] = (
        compra.estado
    )

    return res


def procesar_evento_wompi(
    db: Session,
    transaction: dict,
) -> dict:
    """
    Procesa una transacción recibida desde el webhook de Wompi.

    No requiere un usuario autenticado: la autenticidad de la
    notificación se valida en el endpoint público del webhook.
    Los eventos repetidos para la misma transacción son idempotentes,
    pero permiten actualizar un estado PENDING cuando Wompi notifica
    posteriormente el resultado definitivo.
    """

    transaction_id = transaction.get("id")
    transaction_status = str(
        transaction.get("status", "")
    ).upper()
    reference = transaction.get("reference")
    amount_in_cents = transaction.get("amount_in_cents")
    currency = transaction.get("currency")

    # Validar los datos básicos antes de modificar la base de datos.
    if not isinstance(transaction_id, str) or not transaction_id.strip():
        raise AppError(
            400,
            "La transacción de Wompi no tiene identificador.",
        )

    transaction_id = transaction_id.strip()

    if not isinstance(reference, str) or not reference.strip():
        raise AppError(
            400,
            "La transacción de Wompi no tiene referencia.",
        )

    reference = reference.strip()

    if isinstance(amount_in_cents, bool) or not isinstance(amount_in_cents, int):
        raise AppError(
            400,
            "La transacción de Wompi no tiene un monto válido.",
        )

    if currency != "COP":
        raise AppError(
            400,
            (
                "La moneda recibida en el webhook "
                "no es válida para esta compra."
            ),
        )

    # Buscar el pago asociado a la referencia del checkout.
    pago = (
        db.query(Pago)
        .filter(
            Pago.referencia == reference,
            Pago.metodo == "wompi",
        )
        .first()
    )

    if pago is None:
        raise AppError(
            404,
            (
                "No se encontró un pago asociado "
                "a la referencia de Wompi."
            ),
        )

    compra = (
        db.query(Compra)
        .filter(Compra.id == pago.compra_id)
        .first()
    )

    if compra is None:
        raise AppError(
            404,
            "No se encontró la compra asociada al pago.",
        )

    # Verificar el monto incluso cuando la transacción ya se recibió.
    monto_esperado = int(round(compra.total * 100))
    if amount_in_cents != monto_esperado:
        raise AppError(
            400,
            (
                "El monto recibido de Wompi no coincide "
                "con el monto de la compra."
            ),
        )

    # Un ID de transacción no puede pertenecer a dos pagos diferentes.
    pago_con_transaccion = (
        db.query(Pago)
        .filter(Pago.wompi_transaction_id == transaction_id)
        .first()
    )

    if (
        pago_con_transaccion is not None
        and pago_con_transaccion.id != pago.id
    ):
        raise AppError(
            409,
            (
                "La transacción de Wompi ya está "
                "asociada a otro pago."
            ),
        )

    # Los estados finales no deben retroceder por eventos que lleguen
    # tarde. En particular, PENDING no puede deshacer una aprobación.
    estados_finales = {"APPROVED", "DECLINED", "VOIDED", "ERROR"}
    estado_previo = (pago.wompi_status or "").upper()

    if estado_previo in estados_finales and transaction_status != estado_previo:
        return {
            "ok": True,
            "transactionId": transaction_id,
            "estado": estado_previo,
            "pagoId": str(pago.id),
            "compraId": str(compra.id),
            "compraEstado": compra.estado,
        }

    # Vincular la transacción (o conservar el vínculo existente) y
    # aplicar el estado notificado por Wompi.
    pago.wompi_transaction_id = transaction_id
    pago.wompi_status = transaction_status

    if transaction_status == "APPROVED":
        pago.estado = "APROBADO"
        pago.monto = compra.total
        pago.mensaje_respuesta = (
            "Pago aprobado y confirmado mediante webhook de Wompi."
        )
        compra.estado = "PAGADA"

    elif transaction_status == "DECLINED":
        pago.estado = "RECHAZADO"
        pago.mensaje_respuesta = "El pago fue rechazado por Wompi."
        compra.estado = "RECHAZADO"

    elif transaction_status == "VOIDED":
        pago.estado = "ANULADO"
        pago.mensaje_respuesta = "El pago fue anulado por Wompi."
        compra.estado = "PENDIENTE"

    elif transaction_status == "ERROR":
        pago.estado = "ERROR"
        pago.mensaje_respuesta = "Wompi reportó un error al procesar el pago."
        compra.estado = "ERROR"

    elif transaction_status == "PENDING":
        pago.estado = "PENDIENTE"
        pago.mensaje_respuesta = (
            "El pago se encuentra pendiente de confirmación por Wompi."
        )
        compra.estado = "PENDIENTE"

    else:
        pago.estado = transaction_status or "ERROR"
        pago.mensaje_respuesta = (
            "Wompi devolvió un estado no reconocido."
        )
        compra.estado = "ERROR"

    try:
        db.commit()
        db.refresh(pago)
        db.refresh(compra)
    except Exception:
        db.rollback()
        raise

    return {
        "ok": True,
        "transactionId": transaction_id,
        "estado": transaction_status,
        "pagoId": str(pago.id),
        "compraId": str(compra.id),
        "compraEstado": compra.estado,
    }


def preparar_checkout_wompi(
    db: Session,
    compra_id: uuid.UUID,
    actual: Usuario,
) -> dict:
    """
    Prepara un intento de pago para el Widget de Wompi.

    El monto se obtiene exclusivamente desde la compra
    almacenada en el backend. El frontend no decide
    cuánto se cobra.
    """

    compra = (
        db.query(Compra)
        .filter(
            Compra.id == compra_id
        )
        .first()
    )

    if compra is None:
        raise AppError(
            404,
            "Compra no encontrada.",
        )

    if (
        actual.rol.codigo != "SUPER_ADMINISTRADOR"
        and actual.id != compra.usuario_id
    ):
        raise AppError(
            403,
            "No tiene acceso a esta compra.",
        )

    # ==================================================
    # NO INICIAR OTRO PAGO SI WOMPI AÚN PROCESA UNO
    # ==================================================
    #
    # Evita cobrar dos veces y evita expirar una compra cuyo
    # pago todavía está en proceso. Primero se consulta a Wompi
    # por si el resultado ya es definitivo.

    if compra.estado == "PENDIENTE":
        _reconciliar_pago_pendiente(db, compra)

    if (
        compra.estado == "PENDIENTE"
        and _tiene_pago_en_curso(db, compra)
    ):
        raise AppError(
            400,
            (
                "Esta compra tiene un pago en proceso. "
                "Espera a que Wompi confirme el resultado "
                "antes de intentar pagar de nuevo."
            ),
        )

    # ==================================================
    # VERIFICAR EXPIRACIÓN
    # ==================================================

    if compra.estado == "PENDIENTE":
        limite = (
            compra.creado_en
            + timedelta(
                minutes=TIEMPO_EXPIRACION_COMPRA_MINUTOS
            )
        )

        if utcnow() >= limite:
            compra.estado = "EXPIRADA"
            db.commit()

            raise AppError(
                400,
                (
                    "Esta compra ha expirado. "
                    "Debe crear una nueva compra para "
                    "realizar el pago."
                ),
                compraId=str(compra.id),
                estado=compra.estado,
            )

    # ==================================================
    # VALIDAR ESTADOS QUE NO PUEDEN PAGARSE
    # ==================================================

    if compra.estado == "PAGADA":
        raise AppError(
            400,
            "Esta compra ya ha sido pagada previamente.",
        )

    if compra.estado == "EXPIRADA":
        raise AppError(
            400,
            (
                "Esta compra ha expirado. "
                "Debe crear una nueva compra para "
                "realizar el pago."
            ),
        )

    if compra.estado == "CANCELADA":
        raise AppError(
            400,
            (
                "Esta compra fue cancelada y "
                "no puede continuar con el pago."
            ),
        )

    public_key = (
        wompi_service.get_wompi_public_key()
    )

    if not public_key:
        raise AppError(
            503,
            "La llave pública de Wompi no está configurada.",
        )

    # Wompi recibe el monto en centavos.
    # $11.900 COP => 1.190.000 centavos.
    amount_in_cents = int(
        round(compra.total * 100)
    )

    referencia = (
        f"MSIG-"
        f"{compra.id.hex[:12].upper()}-"
        f"{uuid.uuid4().hex[:12].upper()}"
    )

    firma_integridad = (
        wompi_service.generate_integrity_signature(
            reference=referencia,
            amount_in_cents=amount_in_cents,
            currency="COP",
        )
    )

    pago = Pago(
        compra_id=compra.id,
        metodo="wompi",
        referencia=referencia,
        monto=compra.total,
        estado="PENDIENTE",
        wompi_transaction_id=None,
        wompi_status="PENDING",
        wompi_payment_method=None,
        banco=None,
        ultimos_digitos=None,
        titular=None,
        mensaje_respuesta=(
            "Checkout Wompi preparado. "
            "Pendiente de que el usuario complete el pago."
        ),
    )

    try:
        db.add(pago)
        db.commit()
        db.refresh(pago)

        return {
            "compraId": str(compra.id),
            "pagoId": str(pago.id),
            "reference": referencia,
            "currency": "COP",
            "amountInCents": amount_in_cents,
            "publicKey": public_key,
            "signature": firma_integridad,
            "total": compra.total,
        }

    except Exception:
        db.rollback()
        raise


def cancelar_compra(
    db: Session,
    compra_id: uuid.UUID,
    actual: Usuario,
) -> dict:
    """
    Cancela una compra pendiente.

    Reglas:
    - Solo el propietario de la compra puede cancelarla.
    - El SUPER_ADMINISTRADOR también puede acceder.
    - Solo una compra PENDIENTE puede cancelarse.
    - La compra no se elimina: pasa a CANCELADA
      y permanece en el historial.
    """

    compra = (
        db.query(Compra)
        .filter(
            Compra.id == compra_id
        )
        .first()
    )

    if compra is None:
        raise AppError(
            404,
            "Compra no encontrada.",
        )

    # ==================================================
    # VALIDAR PROPIETARIO
    # ==================================================

    if (
        actual.rol.codigo != "SUPER_ADMINISTRADOR"
        and actual.id != compra.usuario_id
    ):
        raise AppError(
            403,
            "No tiene acceso a esta compra.",
        )

    # ==================================================
    # SOLO SE PUEDE CANCELAR UNA COMPRA PENDIENTE
    # ==================================================

    if compra.estado != "PENDIENTE":
        raise AppError(
            400,
            (
                "Esta compra no puede cancelarse "
                f"porque actualmente está en estado "
                f"{compra.estado}."
            ),
            compraId=str(compra.id),
            estado=compra.estado,
        )

    # ==================================================
    # CANCELAR COMPRA
    # ==================================================

    compra.estado = "CANCELADA"

    try:
        db.commit()
        db.refresh(compra)

    except Exception:
        db.rollback()
        raise

    return _compra_publica(compra)