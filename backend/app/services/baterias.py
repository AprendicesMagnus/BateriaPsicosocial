"""Reglas centrales de disponibilidad y consumo de baterías."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.commercial import Compra
from app.models.evaluation import Evaluacion
from app.models.organization import Organizacion


def saldo_por_organizacion(db: Session, organizacion_id) -> dict:
    if not organizacion_id:
        return {"compradas": 0, "consumidas": 0, "disponibles": 0}

    compradas = (
        db.query(func.coalesce(func.sum(Compra.cantidad), 0))
        .filter(Compra.organizacion_id == organizacion_id, Compra.estado == "PAGADA")
        .scalar() or 0
    )
    consumidas = (
        db.query(func.count(Evaluacion.id))
        .filter(
            Evaluacion.organizacion_id == organizacion_id,
            Evaluacion.bateria_controlada.is_(True),
            Evaluacion.bateria_consumida_en.isnot(None),
        )
        .scalar() or 0
    )
    compradas, consumidas = int(compradas), int(consumidas)
    return {
        "compradas": compradas,
        "consumidas": consumidas,
        "disponibles": max(0, compradas - consumidas),
    }


def consumir_bateria_primera_respuesta(db: Session, participante) -> None:
    """Consume exactamente una batería al guardar la primera respuesta del paciente.

    El bloqueo de la fila de organización serializa el consumo entre distintos enlaces,
    evitando que dos respuestas gasten simultáneamente la última batería.
    No hace commit: forma parte de la misma transacción que guarda la respuesta.
    """
    evaluacion_id = participante.evaluacion_id
    evaluacion = (
        db.query(Evaluacion)
        .filter(Evaluacion.id == evaluacion_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    if evaluacion is None or not evaluacion.bateria_controlada or evaluacion.bateria_consumida_en:
        return

    organizacion = (
        db.query(Organizacion)
        .filter(Organizacion.id == evaluacion.organizacion_id)
        .with_for_update()
        .first()
    )
    if organizacion is None:
        raise AppError(402, "La empresa asociada no tiene una suscripción de baterías disponible.")

    # Volver a comprobar después del bloqueo: otro paciente pudo consumir la última unidad.
    saldo = saldo_por_organizacion(db, evaluacion.organizacion_id)
    if saldo["disponibles"] <= 0:
        raise AppError(402, "La empresa agotó sus baterías. Solicita al administrador que compre un nuevo plan.")

    evaluacion.bateria_consumida_en = utcnow()
