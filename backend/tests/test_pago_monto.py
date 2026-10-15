"""
Tests de validacion de monto y moneda en POST /api/pagos.

El cliente ya no envia el monto: el servicio consulta la transaccion en Wompi
y compara amount_in_cents con compra.total.

1. wompiTransactionId vacio o ausente: HTTP 422 (PagoCreate).
2. Monto de Wompi distinto al total de la compra: HTTP 400 y la compra sigue PENDIENTE.
3. Moneda distinta de COP: HTTP 400.
4. Monto y moneda correctos: HTTP 200, pago APROBADO y compra PAGADA.
"""
import uuid

import pytest

from app.models.commercial import Compra, Pago

PREFIJO_BATERIA_TEST = "Batería Test Pago Monto"


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


@pytest.fixture
def headers_admin(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_compra(client, headers, cantidad=1):
    res = client.post(
        "/api/compras",
        headers=headers,
        json={"cantidad": cantidad, "bateriaNombre": PREFIJO_BATERIA_TEST},
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


def _simular_wompi(monkeypatch, pago, monto_centavos, moneda="COP", status="APPROVED"):
    def _consultar(transaction_id):
        return {
            "data": {
                "id": transaction_id,
                "status": status,
                "reference": pago.referencia,
                "amount_in_cents": monto_centavos,
                "currency": moneda,
            }
        }

    monkeypatch.setattr("app.services.wompi.consultar_transaccion", _consultar)


def test_pago_sin_transaccion_de_wompi_es_rechazado(client, headers_admin):
    """wompiTransactionId vacio o ausente: PagoCreate responde 422."""
    res_vacio = client.post(
        "/api/pagos",
        headers=headers_admin,
        json={"compraId": str(uuid.uuid4()), "wompiTransactionId": ""},
    )
    assert res_vacio.status_code == 422, res_vacio.text

    res_ausente = client.post(
        "/api/pagos",
        headers=headers_admin,
        json={"compraId": str(uuid.uuid4())},
    )
    assert res_ausente.status_code == 422, res_ausente.text


def test_pago_monto_no_coincide_con_total(
    client, db_session, headers_admin, monkeypatch
):
    compra = _crear_compra(client, headers_admin)
    pago = _crear_pago_checkout(db_session, compra)

    monto_incorrecto = int(round(compra["total"] * 100)) - 100000
    _simular_wompi(monkeypatch, pago, monto_incorrecto)

    res = client.post(
        "/api/pagos",
        headers=headers_admin,
        json={"compraId": compra["id"], "wompiTransactionId": "tx-monto-1"},
    )

    assert res.status_code == 400, res.text
    assert "no coincide" in str(res.json()).lower()

    res_compra = client.get(f"/api/compras/{compra['id']}", headers=headers_admin)
    assert res_compra.status_code == 200, res_compra.text
    assert res_compra.json()["estado"] == "PENDIENTE"


def test_pago_moneda_distinta_de_cop_es_rechazado(
    client, db_session, headers_admin, monkeypatch
):
    compra = _crear_compra(client, headers_admin)
    pago = _crear_pago_checkout(db_session, compra)

    _simular_wompi(
        monkeypatch, pago, int(round(compra["total"] * 100)), moneda="USD"
    )

    res = client.post(
        "/api/pagos",
        headers=headers_admin,
        json={"compraId": compra["id"], "wompiTransactionId": "tx-moneda-1"},
    )

    assert res.status_code == 400, res.text
    assert "moneda" in str(res.json()).lower()


def test_pago_monto_correcto_exitoso(
    client, db_session, headers_admin, monkeypatch
):
    compra = _crear_compra(client, headers_admin, cantidad=2)
    pago = _crear_pago_checkout(db_session, compra)

    _simular_wompi(monkeypatch, pago, int(round(compra["total"] * 100)))

    res = client.post(
        "/api/pagos",
        headers=headers_admin,
        json={"compraId": compra["id"], "wompiTransactionId": "tx-monto-ok"},
    )

    assert res.status_code == 200, res.text
    assert res.json()["estado"] == "APROBADO"
    assert res.json()["compraEstado"] == "PAGADA"