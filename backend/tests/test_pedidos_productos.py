import uuid
from datetime import timedelta
import pytest

from app.core.crypto import utcnow
from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.product import Producto
from app.models.product_order import PagoPedidoProducto, PedidoProducto, PedidoProductoItem

PREFIJO_PRODUCTO = "Producto Test 3H"
PASSWORD_USUARIO = "Password1234"


def _borrar_datos_prueba(db_session):
    db_session.rollback()
    pedidos_ids = [
        fila[0]
        for fila in db_session.query(PedidoProductoItem.pedido_id)
        .filter(PedidoProductoItem.nombre_producto.like(f"{PREFIJO_PRODUCTO}%"))
        .distinct()
        .all()
    ]
    for pid in pedidos_ids:
        pedido = db_session.get(PedidoProducto, pid)
        if pedido:
            db_session.delete(pedido)
    if pedidos_ids:
        db_session.commit()

    prods = db_session.query(Producto).filter(Producto.nombre.like(f"{PREFIJO_PRODUCTO}%")).all()
    for prod in prods:
        db_session.delete(prod)
    if prods:
        db_session.commit()


@pytest.fixture(autouse=True)
def _limpiar_datos(db_session):
    _borrar_datos_prueba(db_session)
    yield
    _borrar_datos_prueba(db_session)


@pytest.fixture(autouse=True)
def _bloquear_wompi_red(monkeypatch):
    def _sin_red(*args, **kwargs):
        raise RuntimeError("Estas pruebas no deben consultar a Wompi.")

    monkeypatch.setattr("app.services.wompi.consultar_transaccion", _sin_red)


def _headers_admin(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_organizacion(client, headers_admin, nombre):
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": nombre, "nit": nit})
    assert res.status_code in (200, 201), res.text
    return res.json()["id"]


def _crear_usuario(client, headers_admin, rol_codigo, organizacion_id, password=PASSWORD_USUARIO):
    email = f"{rol_codigo.lower()}_{uuid.uuid4().hex[:8]}@test.com"
    res = client.post(
        "/api/usuarios",
        headers=headers_admin,
        json={
            "nombre": "Prueba",
            "apellido": "Soporte",
            "email": email,
            "password": password,
            "rolCodigo": rol_codigo,
            "organizacionId": organizacion_id,
        },
    )
    assert res.status_code in (200, 201), res.text
    return uuid.UUID(res.json()["id"]), email


def _encabezados_usuario(client, email, password=PASSWORD_USUARIO):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_producto(client, headers_admin, nombre_sufijo="", precio=100000, activo=True):
    nombre = f"{PREFIJO_PRODUCTO} {nombre_sufijo} {uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/productos",
        headers=headers_admin,
        json={
            "nombre": nombre,
            "categoria": "Software",
            "precio": precio,
            "imagen_url": "",
            "activo": activo,
        },
    )
    assert res.status_code in (200, 201), res.text
    return res.json()


def _crear_pago_checkout(db_session, pedido_id, total, transaction_id=None, wompi_status="PENDING"):
    pago = PagoPedidoProducto(
        pedido_id=uuid.UUID(str(pedido_id)),
        metodo="wompi",
        referencia=f"MPROD-TEST-{uuid.uuid4().hex[:12].upper()}",
        monto=total,
        estado="PENDIENTE",
        wompi_transaction_id=transaction_id,
        wompi_status=wompi_status,
    )
    db_session.add(pago)
    db_session.commit()
    db_session.refresh(pago)
    return pago


def _respuesta_wompi(referencia, transaction_id, status, total):
    return {
        "data": {
            "id": transaction_id,
            "status": status,
            "reference": referencia,
            "amount_in_cents": int(round(total * 100)),
            "currency": "COP",
        }
    }


def test_calculo_desde_el_servidor(client):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Calculo", precio=100000)

    res = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 2}]},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["subtotal"] == 200000
    assert data["iva"] == 38000
    assert data["total"] == 238000
    assert data["estado"] == "PENDIENTE"
    assert len(data["items"]) == 1
    assert data["items"][0]["cantidad"] == 2
    assert data["items"][0]["subtotal"] == 200000


def test_producto_inactivo_responde_404_y_no_crea_pedido(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Inactivo", precio=50000, activo=False)

    res = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res.status_code == 404, res.text

    # Verificar que no se creo pedido para ese producto
    item_existente = (
        db_session.query(PedidoProductoItem)
        .filter(PedidoProductoItem.producto_id == uuid.UUID(prod["id"]))
        .first()
    )
    assert item_existente is None


def test_mismo_producto_repetido_se_agrupa(client):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Agrupado", precio=30000)

    res = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={
            "items": [
                {"producto_id": prod["id"], "cantidad": 1},
                {"producto_id": prod["id"], "cantidad": 2},
            ]
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["cantidad"] == 3
    assert data["items"][0]["subtotal"] == 90000


def test_aislamiento_pedidos_entre_usuarios(client):
    headers_admin = _headers_admin(client)
    org_id = _crear_organizacion(client, headers_admin, "Org Pedidos Aislamiento")
    user1_id, email1 = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    _, email2 = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    headers_user1 = _encabezados_usuario(client, email1)
    headers_user2 = _encabezados_usuario(client, email2)

    prod = _crear_producto(client, headers_admin, "Aislamiento", precio=40000)

    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_user1,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido_id = res_crear.json()["id"]

    # Usuario 2 no debe ver el pedido individual ni los pedidos de usuario 1
    res_get_otro = client.get(f"/api/pedidos-productos/{pedido_id}", headers=headers_user2)
    assert res_get_otro.status_code == 403, res_get_otro.text

    res_listar_otro = client.get(f"/api/pedidos-productos/usuario/{user1_id}", headers=headers_user2)
    assert res_listar_otro.status_code == 403, res_listar_otro.text

    # El administrador sí puede ver ambos
    res_get_admin = client.get(f"/api/pedidos-productos/{pedido_id}", headers=headers_admin)
    assert res_get_admin.status_code == 200, res_get_admin.text

    res_listar_admin = client.get(f"/api/pedidos-productos/usuario/{user1_id}", headers=headers_admin)
    assert res_listar_admin.status_code == 200, res_listar_admin.text


def test_cancelar_pedido_pendiente_y_pagada(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Cancelar", precio=25000)

    # Cancelar PENDIENTE sin pagos
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido1_id = res_crear.json()["id"]

    res_cancelar = client.post(f"/api/pedidos-productos/{pedido1_id}/cancelar", headers=headers_admin)
    assert res_cancelar.status_code == 200, res_cancelar.text
    assert res_cancelar.json()["estado"] == "CANCELADA"

    # Cancelar PAGADA responde 400 y estado no cambia
    res_crear2 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear2.status_code == 200, res_crear2.text
    pedido2_id = res_crear2.json()["id"]

    p2 = db_session.get(PedidoProducto, uuid.UUID(pedido2_id))
    p2.estado = "PAGADA"
    db_session.commit()

    res_cancelar2 = client.post(f"/api/pedidos-productos/{pedido2_id}/cancelar", headers=headers_admin)
    assert res_cancelar2.status_code == 400, res_cancelar2.text

    db_session.expire_all()
    p2_check = db_session.get(PedidoProducto, uuid.UUID(pedido2_id))
    assert p2_check.estado == "PAGADA"


def test_checkout_pedido_pendiente(client, db_session, monkeypatch):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Checkout", precio=50000)

    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido = res_crear.json()
    pedido_id = pedido["id"]

    monkeypatch.setattr("app.services.wompi.get_wompi_public_key", lambda: "pub_test_3h")
    monkeypatch.setattr("app.services.wompi.generate_integrity_signature", lambda **kwargs: "firma_test_3h")

    res_checkout = client.post(f"/api/pedidos-productos/{pedido_id}/wompi/checkout", headers=headers_admin)
    assert res_checkout.status_code == 200, res_checkout.text
    data = res_checkout.json()
    assert data["reference"].startswith("MPROD-")
    assert data["amountInCents"] == pedido["total"] * 100
    assert data["currency"] == "COP"
    assert data["publicKey"] == "pub_test_3h"
    assert data["signature"] == "firma_test_3h"

    # Verificar PagoPedidoProducto PENDIENTE en BD
    pago = (
        db_session.query(PagoPedidoProducto)
        .filter(PagoPedidoProducto.referencia == data["reference"])
        .first()
    )
    assert pago is not None
    assert pago.estado == "PENDIENTE"
    assert pago.monto == pedido["total"]


def test_checkout_sobre_pedido_pagado_o_expirado_responde_400(client, db_session, monkeypatch):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Checkout400", precio=60000)

    monkeypatch.setattr("app.services.wompi.get_wompi_public_key", lambda: "pub_test_3h")
    monkeypatch.setattr("app.services.wompi.generate_integrity_signature", lambda **kwargs: "firma_test_3h")

    # Pedido PAGADA
    res1 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    p1_id = res1.json()["id"]
    p1 = db_session.get(PedidoProducto, uuid.UUID(p1_id))
    p1.estado = "PAGADA"
    db_session.commit()

    res_chk1 = client.post(f"/api/pedidos-productos/{p1_id}/wompi/checkout", headers=headers_admin)
    assert res_chk1.status_code == 400, res_chk1.text

    # Pedido EXPIRADA
    res2 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    p2_id = res2.json()["id"]
    p2 = db_session.get(PedidoProducto, uuid.UUID(p2_id))
    p2.estado = "EXPIRADA"
    db_session.commit()

    res_chk2 = client.post(f"/api/pedidos-productos/{p2_id}/wompi/checkout", headers=headers_admin)
    assert res_chk2.status_code == 400, res_chk2.text


def test_expiracion_pedido_vencido_sin_pago_con_transaccion(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Expiracion", precio=70000)

    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido_id = res_crear.json()["id"]

    p = db_session.get(PedidoProducto, uuid.UUID(pedido_id))
    p.creado_en = utcnow() - timedelta(minutes=40)
    db_session.commit()

    # GET lo devuelve EXPIRADA sin llamar a Wompi (el fixture autouse lanzaría RuntimeError si se llamara)
    res_get = client.get(f"/api/pedidos-productos/{pedido_id}", headers=headers_admin)
    assert res_get.status_code == 200, res_get.text
    assert res_get.json()["estado"] == "EXPIRADA"


def test_pedido_vencido_con_pago_en_curso_no_expira(client, db_session, monkeypatch):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "EnCurso", precio=80000)

    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido = res_crear.json()
    pedido_id = pedido["id"]

    pago = _crear_pago_checkout(
        db_session,
        pedido_id,
        pedido["total"],
        transaction_id="tx-3h-curso",
        wompi_status="PENDING",
    )

    p = db_session.get(PedidoProducto, uuid.UUID(pedido_id))
    p.creado_en = utcnow() - timedelta(minutes=40)
    db_session.commit()

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda tx_id: _respuesta_wompi(pago.referencia, tx_id, "PENDING", pedido["total"]),
    )

    res_get = client.get(f"/api/pedidos-productos/{pedido_id}", headers=headers_admin)
    assert res_get.status_code == 200, res_get.text
    assert res_get.json()["estado"] == "PENDIENTE"


def test_confirmacion_pago_por_usuario(client, db_session, monkeypatch):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "ConfPago", precio=90000)

    # 1. Pago confirmado correctamente -> pedido queda PAGADA
    res1 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    p1 = res1.json()
    pago1 = _crear_pago_checkout(db_session, p1["id"], p1["total"])

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda tx_id: _respuesta_wompi(pago1.referencia, tx_id, "APPROVED", p1["total"]),
    )

    res_pago1 = client.post(
        "/api/pedidos-productos/pago",
        headers=headers_admin,
        json={"pedido_id": p1["id"], "wompi_transaction_id": "tx-3h-pago-1"},
    )
    assert res_pago1.status_code == 200, res_pago1.text
    assert res_pago1.json()["pedidoEstado"] == "PAGADA"

    res_get1 = client.get(f"/api/pedidos-productos/{p1['id']}", headers=headers_admin)
    assert res_get1.status_code == 200, res_get1.text
    assert res_get1.json()["estado"] == "PAGADA"

    # 2. Referencia no pertenece al pedido -> 400
    res2 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    p2 = res2.json()
    pago2 = _crear_pago_checkout(db_session, p2["id"], p2["total"])

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda tx_id: _respuesta_wompi("MPROD-OTRA-REFERENCIA", tx_id, "APPROVED", p2["total"]),
    )

    res_pago2 = client.post(
        "/api/pedidos-productos/pago",
        headers=headers_admin,
        json={"pedido_id": p2["id"], "wompi_transaction_id": "tx-3h-pago-2"},
    )
    assert res_pago2.status_code == 400, res_pago2.text

    res_get2 = client.get(f"/api/pedidos-productos/{p2['id']}", headers=headers_admin)
    assert res_get2.status_code == 200, res_get2.text
    assert res_get2.json()["estado"] == "PENDIENTE"

    db_session.expire_all()
    pago2_db = db_session.get(PagoPedidoProducto, pago2.id)
    assert pago2_db.wompi_transaction_id is None
    assert pago2_db.estado == "PENDIENTE"

    # 3. Monto no coincide -> 400 y pedido sigue PENDIENTE
    res3 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    p3 = res3.json()
    pago3 = _crear_pago_checkout(db_session, p3["id"], p3["total"])

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda tx_id: _respuesta_wompi(pago3.referencia, tx_id, "APPROVED", p3["total"] - 50),
    )

    res_pago3 = client.post(
        "/api/pedidos-productos/pago",
        headers=headers_admin,
        json={"pedido_id": p3["id"], "wompi_transaction_id": "tx-3h-pago-3"},
    )
    assert res_pago3.status_code == 400, res_pago3.text

    res_get3 = client.get(f"/api/pedidos-productos/{p3['id']}", headers=headers_admin)
    assert res_get3.status_code == 200, res_get3.text
    assert res_get3.json()["estado"] == "PENDIENTE"

    db_session.expire_all()
    pago3_db = db_session.get(PagoPedidoProducto, pago3.id)
    assert pago3_db.wompi_transaction_id is None
    assert pago3_db.estado == "PENDIENTE"



def test_cancelar_pedido_con_pago_en_curso_pending_responde_400(client, db_session, monkeypatch):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "CancelPending", precio=50000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(
        db_session,
        pedido["id"],
        pedido["total"],
        transaction_id="tx-3h-cancel",
        wompi_status="PENDING",
    )

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda tx_id: _respuesta_wompi(pago.referencia, tx_id, "PENDING", pedido["total"]),
    )

    res_cancelar = client.post(f"/api/pedidos-productos/{pedido['id']}/cancelar", headers=headers_admin)
    assert res_cancelar.status_code == 400, res_cancelar.text
    assert "pago en proceso" in res_cancelar.text.lower()

    res_get = client.get(f"/api/pedidos-productos/{pedido['id']}", headers=headers_admin)
    assert res_get.status_code == 200, res_get.text
    assert res_get.json()["estado"] == "PENDIENTE"


def test_cancelar_pedido_con_pago_en_curso_approved_deja_pagada(client, db_session, monkeypatch):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "CancelApproved", precio=60000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(
        db_session,
        pedido["id"],
        pedido["total"],
        transaction_id="tx-3h-cancel-app",
        wompi_status="PENDING",
    )

    monkeypatch.setattr(
        "app.services.wompi.consultar_transaccion",
        lambda tx_id: _respuesta_wompi(pago.referencia, tx_id, "APPROVED", pedido["total"]),
    )

    res_cancelar = client.post(f"/api/pedidos-productos/{pedido['id']}/cancelar", headers=headers_admin)
    assert res_cancelar.status_code == 400, res_cancelar.text

    res_get = client.get(f"/api/pedidos-productos/{pedido['id']}", headers=headers_admin)
    assert res_get.status_code == 200, res_get.text
    assert res_get.json()["estado"] == "PAGADA"


def test_cancelar_pedido_con_wompi_caido_responde_400(client, db_session, monkeypatch):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "CancelCaido", precio=70000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    _crear_pago_checkout(
        db_session,
        pedido["id"],
        pedido["total"],
        transaction_id="tx-3h-cancel-caido",
        wompi_status="PENDING",
    )

    def _wompi_caido(tx_id):
        raise RuntimeError("Wompi caído.")

    monkeypatch.setattr("app.services.wompi.consultar_transaccion", _wompi_caido)

    res_cancelar = client.post(f"/api/pedidos-productos/{pedido['id']}/cancelar", headers=headers_admin)
    assert res_cancelar.status_code == 400, res_cancelar.text
    assert "pago en proceso" in res_cancelar.text.lower()

    res_get = client.get(f"/api/pedidos-productos/{pedido['id']}", headers=headers_admin)
    assert res_get.status_code == 200, res_get.text
    assert res_get.json()["estado"] == "PENDIENTE"



def test_limite_cantidad_agrupada_mayor_a_99_responde_400(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "LimiteCant", precio=1000)

    res = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={
            "items": [
                {"producto_id": prod["id"], "cantidad": 60},
                {"producto_id": prod["id"], "cantidad": 60},
            ]
        },
    )
    assert res.status_code == 400, res.text
    assert "máxima por producto es 99" in res.text

    item = (
        db_session.query(PedidoProductoItem)
        .filter(PedidoProductoItem.producto_id == uuid.UUID(prod["id"]))
        .first()
    )
    assert item is None


def test_limite_valor_maximo_superado_responde_400(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "SuperaMilMillones", precio=600_000_000)

    res = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 2}]},
    )
    assert res.status_code == 400, res.text
    assert "supera el máximo permitido" in res.text

    item = (
        db_session.query(PedidoProductoItem)
        .filter(PedidoProductoItem.producto_id == uuid.UUID(prod["id"]))
        .first()
    )
    assert item is None


def test_pedido_con_cantidad_exactamente_99_crea_con_200(client):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Exacto99", precio=500)

    res = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 99}]},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["items"][0]["cantidad"] == 99
