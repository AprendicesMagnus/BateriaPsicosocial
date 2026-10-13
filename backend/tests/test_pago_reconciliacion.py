"""
Tests de reconciliación de pagos con Wompi.

Cubren el caso en que el usuario cierra sesión (o la pestaña) mientras
paga y el frontend no alcanza a confirmar la transacción:

1. GET /compras/{id} consulta a Wompi y marca la compra como PAGADA.
2. Una compra vencida con un pago en proceso NO expira.
3. Una compra vencida sin transacción de Wompi sí expira.
4. Si Wompi no responde, la consulta no falla y la compra conserva su estado.
5. POST /pagos acepta una transacción aprobada aunque la compra ya
   haya superado los 30 minutos.
6. No se puede preparar un nuevo checkout mientras Wompi procesa un pago.
"""
import pytest
import uuid
from datetime import timedelta

from app.core.crypto import utcnow
from app.models.commercial import Compra, Pago

PREFIJO_BATERIA_TEST = "Batería Test Reconciliación"


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
    # Antes: borra restos de corridas anteriores. Después: deja limpio.
    _borrar_datos_de_prueba(db_session)
    yield
    _borrar_datos_de_prueba(db_session)
    
def _headers_admin(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_compra(client, headers):
    res = client.post(
        "/api/compras",
        headers=headers,
        json={"cantidad": 1, "bateriaNombre": "Batería Test Reconciliación"},
    )
    assert res.status_code == 200
    return res.json()


def _crear_pago(db_session, compra_id, transaction_id=None):
    pago = Pago(
        compra_id=uuid.UUID(compra_id),
        metodo="wompi",
        referencia=f"MSIG-TEST-{uuid.uuid4().hex[:12].upper()}",
        monto=11900.0,
        estado="PENDIENTE",
        wompi_transaction_id=transaction_id,
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


def _respuesta_wompi(pago, transaction_id, status, total):
    return {
        "data": {
            "id": transaction_id,
            "status": status,
            "reference": pago.referencia,
            "amount_in_cents": int(round(total * 100)),
            "currency": "COP",
        }
    }


def test_obtener_compra_reconcilia_pago_aprobado(client, db_session, monkeypatch):
    headers = _headers_admin(client)
    compra = _crear_compra(client, headers)
    pago = _crear_pago(db_session, compra["id"], transaction_id="tx-rec-1")

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda transaction_id: _respuesta_wompi(
            pago, transaction_id, "APPROVED", compra["total"]
        ),
    )

    res = client.get(f"/api/compras/{compra['id']}", headers=headers)

    assert res.status_code == 200
    assert res.json()["estado"] == "PAGADA"


def test_compra_vencida_con_pago_en_proceso_no_expira(client, db_session, monkeypatch):
    headers = _headers_admin(client)
    compra = _crear_compra(client, headers)
    pago = _crear_pago(db_session, compra["id"], transaction_id="tx-rec-2")
    _vencer_compra(db_session, compra["id"])

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda transaction_id: _respuesta_wompi(
            pago, transaction_id, "PENDING", compra["total"]
        ),
    )

    res = client.get(f"/api/compras/{compra['id']}", headers=headers)

    assert res.status_code == 200
    assert res.json()["estado"] == "PENDIENTE"


def test_compra_vencida_sin_transaccion_expira(client, db_session, monkeypatch):
    headers = _headers_admin(client)
    compra = _crear_compra(client, headers)
    _crear_pago(db_session, compra["id"], transaction_id=None)
    _vencer_compra(db_session, compra["id"])

    def _no_debe_llamarse(transaction_id):
        raise AssertionError("No hay transacción que consultar en Wompi.")

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion", _no_debe_llamarse
    )

    res = client.get(f"/api/compras/{compra['id']}", headers=headers)

    assert res.status_code == 200
    assert res.json()["estado"] == "EXPIRADA"


def test_wompi_caido_no_rompe_la_consulta(client, db_session, monkeypatch):
    headers = _headers_admin(client)
    compra = _crear_compra(client, headers)
    _crear_pago(db_session, compra["id"], transaction_id="tx-rec-4")

    def _wompi_caido(transaction_id):
        raise RuntimeError("No fue posible comunicarse con Wompi.")

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion", _wompi_caido
    )

    res = client.get(f"/api/compras/{compra['id']}", headers=headers)

    assert res.status_code == 200
    assert res.json()["estado"] == "PENDIENTE"


def test_pago_aprobado_se_acepta_aunque_la_compra_haya_vencido(
    client, db_session, monkeypatch
):
    headers = _headers_admin(client)
    compra = _crear_compra(client, headers)
    pago = _crear_pago(db_session, compra["id"], transaction_id=None)
    _vencer_compra(db_session, compra["id"])

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda transaction_id: _respuesta_wompi(
            pago, transaction_id, "APPROVED", compra["total"]
        ),
    )

    res = client.post(
        "/api/pagos",
        headers=headers,
        json={
            "compraId": compra["id"],
            "wompiTransactionId": "tx-rec-5",
        },
    )

    assert res.status_code == 200
    assert res.json()["estado"] == "APROBADO"
    assert res.json()["compraEstado"] == "PAGADA"


def test_no_se_prepara_otro_checkout_con_pago_en_proceso(
    client, db_session, monkeypatch
):
    headers = _headers_admin(client)
    compra = _crear_compra(client, headers)
    pago = _crear_pago(db_session, compra["id"], transaction_id="tx-rec-6")

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda transaction_id: _respuesta_wompi(
            pago, transaction_id, "PENDING", compra["total"]
        ),
    )

    res = client.post(
        f"/api/compras/{compra['id']}/wompi/checkout",
        headers=headers,
    )

    assert res.status_code == 400
    assert "en proceso" in str(res.json()).lower()