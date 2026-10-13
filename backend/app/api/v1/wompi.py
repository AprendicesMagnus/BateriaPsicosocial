from json import JSONDecodeError

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import compras as compras_service
from app.services import wompi as wompi_service


router = APIRouter()


@router.post("/events")
async def recibir_evento_wompi(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Endpoint público para recibir eventos de Wompi.

    Wompi utiliza este endpoint para notificar cambios
    en el estado de las transacciones.

    La autenticidad del evento se valida mediante la firma
    enviada por Wompi antes de procesar cualquier transacción.
    """

    try:
        payload = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="El cuerpo de la solicitud no contiene JSON válido.",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="El cuerpo de la solicitud debe ser un objeto JSON.",
        )

    evento = payload.get("event")
    data = payload.get("data")

    if not evento or not isinstance(evento, str):
        raise HTTPException(
            status_code=400,
            detail="Evento no especificado.",
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="Datos del evento no especificados.",
        )

    transaction = data.get("transaction")

    if not isinstance(transaction, dict) or not transaction:
        raise HTTPException(
            status_code=400,
            detail="Transacción no especificada.",
        )

    signature = payload.get("signature")

    if not isinstance(signature, dict):
        raise HTTPException(
            status_code=401,
            detail="Firma del evento incompleta.",
        )

    properties = signature.get("properties")
    checksum = signature.get("checksum")
    timestamp = payload.get("timestamp")

    if not isinstance(properties, list) or not properties:
        raise HTTPException(
            status_code=401,
            detail="Propiedades de firma incompletas.",
        )

    if not isinstance(checksum, str) or not checksum.strip():
        raise HTTPException(
            status_code=401,
            detail="Firma del evento incompleta.",
        )

    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise HTTPException(
            status_code=401,
            detail="Timestamp de firma inválido.",
        )

    try:
        firma_valida = wompi_service.validar_firma_evento(
            properties=properties,
            signature_checksum=checksum,
            timestamp=timestamp,
            data=data,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="El servicio de validación de eventos no está configurado.",
        ) from exc

    if not firma_valida:
        raise HTTPException(
            status_code=401,
            detail="Firma del evento no válida.",
        )

    transaction_id = transaction.get("id")

    if not isinstance(transaction_id, str) or not transaction_id.strip():
        raise HTTPException(
            status_code=400,
            detail="ID de transacción no especificado.",
        )

    transaction_status = transaction.get("status", "")

    if not isinstance(transaction_status, str):
        raise HTTPException(
            status_code=400,
            detail="Estado de transacción inválido.",
        )

    transaction_status = transaction_status.upper()

    resultado = compras_service.procesar_evento_wompi(
        db=db,
        transaction=transaction,
    )

    return {
        "ok": True,
        "evento": evento,
        "transactionId": transaction_id,
        "estado": transaction_status,
        "pagoId": resultado["pagoId"],
        "compraId": resultado["compraId"],
        "compraEstado": resultado["compraEstado"],
    }