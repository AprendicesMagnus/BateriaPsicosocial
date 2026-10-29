import hashlib
import threading
import time
import uuid
from datetime import timedelta
import pytest
from sqlalchemy.orm import sessionmaker

from app.core.crypto import utcnow
from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.commercial import Compra, Pago
from app.models.product import Producto
from app.models.product_order import PagoPedidoProducto, PedidoProducto, PedidoProductoItem

PREFIJO_PRODUCTO = "Producto Test 3H"
PREFIJO_BATERIA = "Batería Test 3H"
PASSWORD_USUARIO = "Password1234"
EVENTS_SECRET_TEST = "https://decrease-oxidant-reassign.ngrok-free.dev/api/wompi/events"
PROPIEDADES_FIRMA = [
    "transaction.id",
    "transaction.status",
    "transaction.amount_in_cents",
]


def _borrar_datos_prueba(db_session):
    db_session.rollback()

    # Limpiar pedidos de productos
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

    # Limpiar productos
    prods = db_session.query(Producto).filter(Producto.nombre.like(f"{PREFIJO_PRODUCTO}%")).all()
    for prod in prods:
        db_session.delete(prod)
    if prods:
        db_session.commit()

    # Limpiar compras y pagos comerciales
    compras_ids = [
        fila[0]
        for fila in db_session.query(Compra.id)
        .filter(Compra.bateria_nombre.like(f"{PREFIJO_BATERIA}%"))
        .all()
    ]
    if compras_ids:
        db_session.query(Pago).filter(Pago.compra_id.in_(compras_ids)).delete(synchronize_session=False)
        db_session.query(Compra).filter(Compra.id.in_(compras_ids)).delete(synchronize_session=False)
        db_session.commit()


@pytest.fixture(autouse=True)
def _limpiar_datos(db_session):
    _borrar_datos_prueba(db_session)
    yield
    _borrar_datos_prueba(db_session)


@pytest.fixture(autouse=True)
def _configuracion_wompi_webhook(monkeypatch):
    monkeypatch.setattr(
        "app.services.wompi.get_wompi_events_secret",
        lambda: EVENTS_SECRET_TEST,
    )

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


def _crear_producto(client, headers_admin, nombre_sufijo="", precio=100000):
    nombre = f"{PREFIJO_PRODUCTO} {nombre_sufijo} {uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/productos",
        headers=headers_admin,
        json={
            "nombre": nombre,
            "categoria": "Software",
            "precio": precio,
            "imagen_url": "",
            "activo": True,
            "stock": 100,
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


def _evento(pago_o_ref, total, transaction_id, status, monto_centavos=None, firma_valida=True):
    referencia = pago_o_ref if isinstance(pago_o_ref, str) else pago_o_ref.referencia
    if monto_centavos is None:
        monto_centavos = int(round(total * 100))

    transaction = {
        "id": transaction_id,
        "status": status,
        "reference": referencia,
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


def _contar_notificaciones_compra(client, headers):
    res = client.get("/api/notificaciones", headers=headers)
    assert res.status_code == 200, res.text
    return [n for n in res.json() if n["tipo"] == "COMPRA_APROBADA"]


def test_approved_con_firma_valida(client, db_session):
    headers_admin = _headers_admin(client)
    org_id = _crear_organizacion(client, headers_admin, "Org Webhook 1")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    headers_user = _encabezados_usuario(client, email_user)

    prod = _crear_producto(client, headers_admin, "WH1", precio=80000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_user,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    notis_antes = len(_contar_notificaciones_compra(client, headers_user))

    ev = _evento(pago, pedido["total"], "tx-wh-a", "APPROVED")
    res_ev = client.post("/api/wompi/events", json=ev)
    assert res_ev.status_code == 200, res_ev.text
    assert res_ev.json()["pedidoEstado"] == "PAGADA"

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PAGADA"

    pago_db = db_session.get(PagoPedidoProducto, pago.id)
    assert pago_db.estado == "APROBADO"
    assert pago_db.wompi_transaction_id == "tx-wh-a"

    notis_despues = _contar_notificaciones_compra(client, headers_user)
    assert len(notis_despues) - notis_antes == 1


def test_firma_invalida_responde_401(client, db_session):
    headers_admin = _headers_admin(client)
    org_id = _crear_organizacion(client, headers_admin, "Org Webhook 2")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    headers_user = _encabezados_usuario(client, email_user)

    prod = _crear_producto(client, headers_admin, "WH2", precio=75000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_user,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    notis_antes = len(_contar_notificaciones_compra(client, headers_user))

    ev = _evento(pago, pedido["total"], "tx-wh-b", "APPROVED", firma_valida=False)
    res_ev = client.post("/api/wompi/events", json=ev)
    assert res_ev.status_code == 401, res_ev.text

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PENDIENTE"

    notis_despues = _contar_notificaciones_compra(client, headers_user)
    assert len(notis_despues) == notis_antes


def test_evento_approved_repetido_es_idempotente(client, db_session):
    headers_admin = _headers_admin(client)
    org_id = _crear_organizacion(client, headers_admin, "Org Webhook 3")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    headers_user = _encabezados_usuario(client, email_user)

    prod = _crear_producto(client, headers_admin, "WH3", precio=60000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_user,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    notis_antes = len(_contar_notificaciones_compra(client, headers_user))

    ev = _evento(pago, pedido["total"], "tx-wh-c", "APPROVED")
    res1 = client.post("/api/wompi/events", json=ev)
    res2 = client.post("/api/wompi/events", json=ev)

    assert res1.status_code == 200, res1.text
    assert res2.status_code == 200, res2.text

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PAGADA"

    notis_despues = _contar_notificaciones_compra(client, headers_user)
    assert len(notis_despues) - notis_antes == 1


def test_monto_distinto_responde_400(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "WH4", precio=50000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    monto_incorrecto = (pedido["total"] * 100) - 1000
    ev = _evento(pago, pedido["total"], "tx-wh-d", "APPROVED", monto_centavos=monto_incorrecto)
    res_ev = client.post("/api/wompi/events", json=ev)
    assert res_ev.status_code == 400, res_ev.text

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PENDIENTE"


def test_pending_tardio_no_deshace_aprobacion(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "WH5", precio=95000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    ev_app = _evento(pago, pedido["total"], "tx-wh-e", "APPROVED")
    res_app = client.post("/api/wompi/events", json=ev_app)
    assert res_app.status_code == 200, res_app.text

    ev_pen = _evento(pago, pedido["total"], "tx-wh-e", "PENDING")
    res_pen = client.post("/api/wompi/events", json=ev_pen)
    assert res_pen.status_code == 200, res_pen.text

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PAGADA"


def test_declined_marca_pedido_y_pago_rechazados(client, db_session):
    headers_admin = _headers_admin(client)
    org_id = _crear_organizacion(client, headers_admin, "Org Webhook 6")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    headers_user = _encabezados_usuario(client, email_user)

    prod = _crear_producto(client, headers_admin, "WH6", precio=45000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_user,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    notis_antes = len(_contar_notificaciones_compra(client, headers_user))

    ev_dec = _evento(pago, pedido["total"], "tx-wh-f", "DECLINED")
    res_dec = client.post("/api/wompi/events", json=ev_dec)
    assert res_dec.status_code == 200, res_dec.text

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "RECHAZADO"

    pago_db = db_session.get(PagoPedidoProducto, pago.id)
    assert pago_db.estado == "RECHAZADO"

    notis_despues = _contar_notificaciones_compra(client, headers_user)
    assert len(notis_despues) == notis_antes


def test_approved_sobre_pedido_expirado_lo_deja_pagado(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "WH7", precio=70000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    p_db.creado_en = utcnow() - timedelta(minutes=40)
    p_db.estado = "EXPIRADA"
    db_session.commit()

    ev = _evento(pago, pedido["total"], "tx-wh-g", "APPROVED")
    res_ev = client.post("/api/wompi/events", json=ev)
    assert res_ev.status_code == 200, res_ev.text

    db_session.expire_all()
    p_check = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_check.estado == "PAGADA"


def test_referencia_mprod_inexistente_responde_404(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "Inexistente", precio=50000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    ev = _evento("MPROD-TEST-NOEXISTE", pedido["total"], "tx-wh-h", "APPROVED")
    res_ev = client.post("/api/wompi/events", json=ev)
    assert res_ev.status_code == 404, res_ev.text

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PENDIENTE"

    pago_db = db_session.get(PagoPedidoProducto, pago.id)
    assert pago_db.wompi_transaction_id is None
    assert pago_db.wompi_status == "PENDING"
    assert pago_db.estado == "PENDIENTE"

    pago_con_tx = (
        db_session.query(PagoPedidoProducto)
        .filter(PagoPedidoProducto.wompi_transaction_id == "tx-wh-h")
        .first()
    )
    assert pago_con_tx is None


def test_transaccion_id_duplicado_responde_409(client, db_session):
    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "WH9", precio=35000)

    # Pedido 1 y pago 1
    res1 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    p1 = res1.json()
    pago1 = _crear_pago_checkout(db_session, p1["id"], p1["total"])

    # Pedido 2 y pago 2
    res2 = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    p2 = res2.json()
    pago2 = _crear_pago_checkout(db_session, p2["id"], p2["total"])

    # Evento para pago 1 con id tx-3h-dup
    ev1 = _evento(pago1, p1["total"], "tx-3h-dup", "APPROVED")
    res_ev1 = client.post("/api/wompi/events", json=ev1)
    assert res_ev1.status_code == 200, res_ev1.text

    # Evento para pago 2 con el mismo id tx-3h-dup -> 409
    ev2 = _evento(pago2, p2["total"], "tx-3h-dup", "APPROVED")
    res_ev2 = client.post("/api/wompi/events", json=ev2)
    assert res_ev2.status_code == 409, res_ev2.text


def test_separacion_de_flujos_pedido_y_compra(client, db_session):
    headers_admin = _headers_admin(client)

    # Crear pedido de productos
    prod = _crear_producto(client, headers_admin, "WH10", precio=40000)
    res_ped = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_ped.json()
    pago_pedido = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    # Crear compra comercial (PENDIENTE)
    res_compra = client.post(
        "/api/compras",
        headers=headers_admin,
        json={"cantidad": 1, "bateriaNombre": f"{PREFIJO_BATERIA} Webhook"},
    )
    assert res_compra.status_code == 200, res_compra.text
    compra = res_compra.json()

    # Enviar evento APPROVED con referencia MPROD- para el pedido
    ev = _evento(pago_pedido, pedido["total"], "tx-wh-j", "APPROVED")
    res_ev = client.post("/api/wompi/events", json=ev)
    assert res_ev.status_code == 200, res_ev.text

    # Verificar que el pedido pasó a PAGADA
    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PAGADA"

    # Verificar que la compra sigue PENDIENTE
    res_get_compra = client.get(f"/api/compras/{compra['id']}", headers=headers_admin)
    assert res_get_compra.status_code == 200, res_get_compra.text
    assert res_get_compra.json()["estado"] == "PENDIENTE"



def test_bloqueo_for_update_al_procesar_evento(client, db_session):
    import sqlalchemy.event as sa_event

    headers_admin = _headers_admin(client)
    prod = _crear_producto(client, headers_admin, "ForUpdate", precio=45000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_admin,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    sentencias = []

    def _capturar_sql(conn, cursor, statement, parameters, context, executemany):
        sentencias.append(statement)

    engine = db_session.get_bind()
    sa_event.listen(engine, "before_cursor_execute", _capturar_sql)

    try:
        ev = _evento(pago, pedido["total"], "tx-wh-k-forupdate", "APPROVED")
        res_ev = client.post("/api/wompi/events", json=ev)
        assert res_ev.status_code == 200, res_ev.text
    finally:
        sa_event.remove(engine, "before_cursor_execute", _capturar_sql)

    coincidencias = [
        s for s in sentencias
        if "FOR UPDATE" in s.upper() and "pedidos_productos" in s.lower()
    ]
    assert len(coincidencias) > 0, f"No se encontró sentencia con FOR UPDATE y pedidos_productos en: {sentencias}"

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, uuid.UUID(pedido["id"]))
    assert p_db.estado == "PAGADA"


def test_numero_pedido_coherente_en_notificacion(client, db_session):
    headers_admin = _headers_admin(client)
    org_id = _crear_organizacion(client, headers_admin, "Org Webhook 12")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    headers_user = _encabezados_usuario(client, email_user)

    prod = _crear_producto(client, headers_admin, "WH12", precio=55000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_user,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    pedido = res_crear.json()
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    notis_antes = len(_contar_notificaciones_compra(client, headers_user))

    ev = _evento(pago, pedido["total"], "tx-wh-l-notif", "APPROVED")
    res_ev = client.post("/api/wompi/events", json=ev)
    assert res_ev.status_code == 200, res_ev.text

    res_get = client.get(f"/api/pedidos-productos/{pedido['id']}", headers=headers_user)
    assert res_get.status_code == 200, res_get.text
    numero = res_get.json()["numero"]

    notis_despues = _contar_notificaciones_compra(client, headers_user)
    assert len(notis_despues) - notis_antes == 1
    nueva_noti = notis_despues[0]
    assert nueva_noti["mensaje"] == f"Tu pedido {numero} fue pagado correctamente."



def test_bloqueo_real_de_fila_serializa_eventos_concurrentes(client, db_session):
    headers_admin = _headers_admin(client)
    org_id = _crear_organizacion(client, headers_admin, "Org Webhook Bloqueo")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id)
    headers_user = _encabezados_usuario(client, email_user)

    prod = _crear_producto(client, headers_admin, "Bloqueo", precio=65000)
    res_crear = client.post(
        "/api/pedidos-productos",
        headers=headers_user,
        json={"items": [{"producto_id": prod["id"], "cantidad": 1}]},
    )
    assert res_crear.status_code == 200, res_crear.text
    pedido = res_crear.json()
    pedido_uuid = uuid.UUID(pedido["id"])
    pago = _crear_pago_checkout(db_session, pedido["id"], pedido["total"])

    notis_antes = len(_contar_notificaciones_compra(client, headers_user))
    evento = _evento(pago, pedido["total"], "tx-wh-bloqueo", "APPROVED")

    sesion_externa = sessionmaker(bind=db_session.get_bind())()
    resultado = {}

    def _enviar_evento():
        try:
            resultado["respuesta"] = client.post("/api/wompi/events", json=evento)
        except Exception as exc:
            resultado["error"] = exc

    hilo = threading.Thread(target=_enviar_evento, daemon=True)
    try:
        # Otra conexion toma el candado de la fila del pedido.
        bloqueado = (
            sesion_externa.query(PedidoProducto)
            .filter(PedidoProducto.id == pedido_uuid)
            .with_for_update()
            .first()
        )
        assert bloqueado is not None

        hilo.start()
        time.sleep(1.5)
        assert hilo.is_alive(), "El evento no esperó al candado de la fila: no hay serialización."

        # La otra conexion termina de pagar el pedido y libera el candado.
        bloqueado.estado = "PAGADA"
        sesion_externa.commit()
        hilo.join(timeout=15)
        assert not hilo.is_alive(), "El evento no terminó después de liberar el candado."
    finally:
        sesion_externa.rollback()
        sesion_externa.close()
        if hilo.is_alive():
            hilo.join(timeout=15)

    assert "error" not in resultado, resultado.get("error")
    assert resultado["respuesta"].status_code == 200, resultado["respuesta"].text

    db_session.expire_all()
    p_db = db_session.get(PedidoProducto, pedido_uuid)
    assert p_db.estado == "PAGADA"
    pago_db = db_session.get(PagoPedidoProducto, pago.id)
    assert pago_db.estado == "APROBADO"
    assert pago_db.wompi_transaction_id == "tx-wh-bloqueo"

    # El pedido ya estaba pagado cuando el evento obtuvo el candado: no se duplica el aviso.
    notis_despues = _contar_notificaciones_compra(client, headers_user)
    assert len(notis_despues) == notis_antes
