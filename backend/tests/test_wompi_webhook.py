"""
Tests del webhook de Wompi (POST /api/wompi/events).

El webhook confirma pagos sin depender de la sesion del usuario: si el usuario
cierra sesion antes de que el widget informe la transaccion al backend, el pago
se vincula por la referencia y la compra se marca como PAGADA.

1. Evento APPROVED sobre una compra vencida: la compra queda PAGADA.
2. Firma invalida: HTTP 401 y la compra no cambia.
3. Evento repetido: idempotente.
4. Monto distinto al total de la compra: HTTP 400 y la compra no cambia.
5. Un PENDING tardio no deshace una aprobacion.
"""
import hashlib
import time
import uuid
from datetime import timedelta

import pytest

from app.core.crypto import utcnow
from app.models.commercial import Compra, Pago

PREFIJO_BATERIA_TEST = "Batería Test Webhook"
EVENTS_SECRET_TEST = "https://decrease-oxidant-reassign.ngrok-free.dev/api/wompi/events"
PROPIEDADES_FIRMA = [
    "transaction.id",
    "transaction.status",
    "transaction.amount_in_cents",
]


def _borrar_datos_de_prueba(db_session):
    db_session.rollback()
    ids = [
        fila.id
        for fila in db_session.query(Compra.id).filter(
            Compra.bateria_nombre.like(f"{PREFIJO_BATERIA_TEST}%")
        )
    ]
    if ids:
        db_session.query(Pago).filter(Pago.compra_id.in_(ids)).delete(
            synchronize_session=False
        )
        db_session.query(Compra).filter(Compra.id.in_(ids)).delete(
            synchronize_session=False
        )
        db_session.commit()


@pytest.fixture(autouse=True)
def _limpiar_compras_de_prueba(db_session):
    _borrar_datos_de_prueba(db_session)
    yield
    _borrar_datos_de_prueba(db_session)


@pytest.fixture(autouse=True)
def _secreto_de_eventos(monkeypatch):
    monkeypatch.setattr(
        "app.services.wompi.get_wompi_events_secret",
        lambda: EVENTS_SECRET_TEST,
    )

    def _sin_red(transaction_id):
        raise RuntimeError("Estos tests no deben consultar a Wompi.")

    monkeypatch.setattr("app.services.wompi.consultar_transaccion", _sin_red)


@pytest.fixture
def headers_admin(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_compra(client, headers):
    res = client.post(
        "/api/compras",
        headers=headers,
        json={"cantidad": 1, "bateriaNombre": PREFIJO_BATERIA_TEST},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _crear_pago_checkout(db_session, compra):
    """Pago PENDIENTE sin transaccion, como el que deja el checkout de Wompi."""
    pago = Pago(
        compra_id=uuid.UUID(compra["id"]),
        metodo="wompi",
        referencia=f"MSIG-TEST-{uuid.uuid4().hex[:12].upper()}",
        monto=compra["total"],
        estado="PENDIENTE",
        wompi_transaction_id=None,
        wompi_status="PENDING",
    )
    db_session.add(pago)
    db_session.commit()
    db_session.refresh(pago)
    return pago


def _vencer_compra(db_session, compra_id):
    compra = db_session.get(Compra, uuid.UUID(compra_id))
    compra.creado_en = utcnow() - timedelta(minutes=40)
    db_session.commit()


def _evento(pago, compra, transaction_id, status, monto_centavos=None, firma_valida=True):
    if monto_centavos is None:
        monto_centavos = int(round(compra["total"] * 100))

    transaction = {
        "id": transaction_id,
        "status": status,
        "reference": pago.referencia,
        "amount_in_cents": monto_centavos,
        "currency": "COP",
    }
    timestamp = int(time.time())
    valores = f"{transaction_id}{status}{monto_centavos}"
    checksum = hashlib.sha256(
        f"{valores}{timestamp}{EVENTS_SECRET_TEST}".encode("utf-8")
    ).hexdigest()
    if not firma_valida:
        checksum = "0" * 64

    return {
        "event": "transaction.updated",
        "data": {"transaction": transaction},
        "timestamp": timestamp,
        "signature": {"properties": PROPIEDADES_FIRMA, "checksum": checksum},
    }


def _estado_compra(client, headers, compra_id):
    res = client.get(f"/api/compras/{compra_id}", headers=headers)
    assert res.status_code == 200, res.text
    return res.json()["estado"]


def test_evento_aprobado_marca_pagada_una_compra_vencida(
    client, db_session, headers_admin
):
    compra = _crear_compra(client, headers_admin)
    pago = _crear_pago_checkout(db_session, compra)
    _vencer_compra(db_session, compra["id"])

    res = client.post(
        "/api/wompi/events", json=_evento(pago, compra, "tx-wh-1", "APPROVED")
    )

    assert res.status_code == 200, res.text
    assert res.json()["compraEstado"] == "PAGADA"
    assert _estado_compra(client, headers_admin, compra["id"]) == "PAGADA"

    db_session.expire_all()
    pago_guardado = db_session.get(Pago, pago.id)
    assert pago_guardado.wompi_transaction_id == "tx-wh-1"
    assert pago_guardado.estado == "APROBADO"


def test_evento_con_firma_invalida_es_rechazado(client, db_session, headers_admin):
    compra = _crear_compra(client, headers_admin)
    pago = _crear_pago_checkout(db_session, compra)

    res = client.post(
        "/api/wompi/events",
        json=_evento(pago, compra, "tx-wh-2", "APPROVED", firma_valida=False),
    )

    assert res.status_code == 401, res.text
    assert _estado_compra(client, headers_admin, compra["id"]) == "PENDIENTE"


def test_evento_repetido_es_idempotente(client, db_session, headers_admin):
    compra = _crear_compra(client, headers_admin)
    pago = _crear_pago_checkout(db_session, compra)
    evento = _evento(pago, compra, "tx-wh-3", "APPROVED")

    res_1 = client.post("/api/wompi/events", json=evento)
    res_2 = client.post("/api/wompi/events", json=evento)

    assert res_1.status_code == 200, res_1.text
    assert res_2.status_code == 200, res_2.text
    assert res_2.json()["compraEstado"] == "PAGADA"
    assert _estado_compra(client, headers_admin, compra["id"]) == "PAGADA"


def test_evento_con_monto_distinto_es_rechazado(client, db_session, headers_admin):
    compra = _crear_compra(client, headers_admin)
    pago = _crear_pago_checkout(db_session, compra)
    monto_incorrecto = int(round(compra["total"] * 100)) - 100000

    res = client.post(
        "/api/wompi/events",
        json=_evento(
            pago, compra, "tx-wh-4", "APPROVED", monto_centavos=monto_incorrecto
        ),
    )

    assert res.status_code == 400, res.text
    assert _estado_compra(client, headers_admin, compra["id"]) == "PENDIENTE"


def test_evento_pending_tardio_no_deshace_la_aprobacion(
    client, db_session, headers_admin
):
    compra = _crear_compra(client, headers_admin)
    pago = _crear_pago_checkout(db_session, compra)

    res_aprobado = client.post(
        "/api/wompi/events", json=_evento(pago, compra, "tx-wh-5", "APPROVED")
    )
    assert res_aprobado.status_code == 200, res_aprobado.text

    res_tardio = client.post(
        "/api/wompi/events", json=_evento(pago, compra, "tx-wh-5", "PENDING")
    )

    assert res_tardio.status_code == 200, res_tardio.text
    assert res_tardio.json()["compraEstado"] == "PAGADA"
    assert _estado_compra(client, headers_admin, compra["id"]) == "PAGADA"