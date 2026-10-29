import uuid
import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.audit import Auditoria
from app.models.commercial import Compra
from app.models.evaluation import Notificacion
from app.models.product_order import PedidoProducto, PedidoProductoItem
from app.models.ticket_soporte import TicketSoporte
from app.models.user import Usuario
from app.services.derechos_titular import PREFIJO_SOLICITUD_ELIMINACION

PASSWORD_USUARIO = "Password1234"


def _encabezados(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_organizacion(client, headers_admin, nombre):
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": nombre, "nit": nit})
    assert res.status_code in (200, 201), res.text
    return res.json()["id"]


def _crear_usuario(client, headers_admin, rol_codigo, organizacion_id, password, nombre="Prueba", apellido="Soporte"):
    email = f"{rol_codigo.lower()}_{uuid.uuid4().hex[:8]}@test.com"
    res = client.post(
        "/api/usuarios",
        headers=headers_admin,
        json={
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "password": password,
            "rolCodigo": rol_codigo,
            "organizacionId": organizacion_id,
        },
    )
    assert res.status_code in (200, 201), res.text
    return uuid.UUID(res.json()["id"]), email


def test_descargar_datos_requiere_sesion(client):
    res = client.get("/api/usuarios/me/datos")
    assert res.status_code == 401


def test_descargar_datos_devuelve_solo_datos_propios_y_audita(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, f"Org Derechos {uuid.uuid4().hex[:6]}")
    user_a_id, email_a = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    user_b_id, email_b = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)

    headers_a = _encabezados(client, email_a, PASSWORD_USUARIO)
    headers_b = _encabezados(client, email_b, PASSWORD_USUARIO)

    mensaje_a = f"Mensaje confidencial de usuario A {uuid.uuid4().hex}"
    mensaje_b = f"Mensaje privado exclusivo de usuario B {uuid.uuid4().hex}"

    res_msg_a = client.post("/api/soporte", headers=headers_a, json={"mensaje": mensaje_a})
    assert res_msg_a.status_code == 200, res_msg_a.text

    res_msg_b = client.post("/api/soporte", headers=headers_b, json={"mensaje": mensaje_b})
    assert res_msg_b.status_code == 200, res_msg_b.text

    res = client.get("/api/usuarios/me/datos", headers=headers_a)
    assert res.status_code == 200, res.text

    disp = res.headers.get("content-disposition", "")
    assert "attachment" in disp
    assert ".json" in disp

    data = res.json()
    assert data["cuenta"]["email"] == email_a

    mensajes_exportados = [m["mensaje"] for m in data.get("mensajesSoporte", [])]
    assert mensaje_a in mensajes_exportados
    assert mensaje_b not in res.text

    texto_lower = res.text.lower()
    assert "password" not in texto_lower
    assert "hash" not in texto_lower

    auditoria = (
        db_session.query(Auditoria)
        .filter(Auditoria.usuario_id == user_a_id, Auditoria.accion == "DATOS_DESCARGADOS")
        .first()
    )
    assert auditoria is not None, "Debe existir un registro de auditoria DATOS_DESCARGADOS para el usuario A"


def test_descargar_datos_incluye_compras_y_pedidos_propios(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, f"Org Compras {uuid.uuid4().hex[:6]}")
    user_a_id, email_a = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    user_b_id, email_b = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)

    headers_a = _encabezados(client, email_a, PASSWORD_USUARIO)

    compra_a = Compra(
        usuario_id=user_a_id,
        bateria_nombre="Batería de Riesgo Psicosocial",
        cantidad=2,
        tarifa_unitario=10000.0,
        subtotal=20000.0,
        iva=3800.0,
        total=23800.0,
        estado="APROBADA",
    )
    db_session.add(compra_a)

    pedido_a = PedidoProducto(
        usuario_id=user_a_id,
        subtotal=10000,
        iva=1900,
        total=11900,
        estado="PAGADA",
    )
    db_session.add(pedido_a)
    db_session.flush()

    item_a = PedidoProductoItem(
        pedido_id=pedido_a.id,
        nombre_producto="Producto de prueba",
        precio_unitario=10000,
        cantidad=1,
        subtotal=10000,
    )
    db_session.add(item_a)

    compra_b = Compra(
        usuario_id=user_b_id,
        bateria_nombre="Batería Ajena B",
        cantidad=5,
        tarifa_unitario=10000.0,
        subtotal=50000.0,
        iva=9500.0,
        total=59500.0,
        estado="APROBADA",
    )
    db_session.add(compra_b)
    db_session.commit()

    res = client.get("/api/usuarios/me/datos", headers=headers_a)
    assert res.status_code == 200, res.text
    data = res.json()

    compras = data.get("compras", [])
    assert len(compras) == 1
    assert compras[0]["cantidad"] == 2
    assert compras[0]["subtotal"] == 20000.0

    pedidos = data.get("pedidosProductos", [])
    assert len(pedidos) == 1
    assert pedidos[0]["numero"].startswith("PED-")
    assert len(pedidos[0]["items"]) == 1
    assert pedidos[0]["items"][0]["producto"] == "Producto de prueba"

    assert "Batería Ajena B" not in res.text


def test_solicitar_eliminacion_crea_mensaje_audita_y_avisa_al_admin(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, f"Org Solicitud {uuid.uuid4().hex[:6]}")
    apellido_unico = "Apellido" + "".join(chr(65 + int(c, 16)) for c in uuid.uuid4().hex[:8])
    user_id, email = _crear_usuario(
        client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO, nombre="Laura", apellido=apellido_unico
    )
    headers_user = _encabezados(client, email, PASSWORD_USUARIO)

    motivo = "Ya no uso la plataforma"
    res = client.post("/api/usuarios/me/solicitar-eliminacion", headers=headers_user, json={"motivo": motivo})
    assert res.status_code == 200, res.text

    res_mios = client.get("/api/soporte/mios", headers=headers_user)
    assert res_mios.status_code == 200, res_mios.text
    tickets = [t for t in res_mios.json() if t["mensaje"].startswith(PREFIJO_SOLICITUD_ELIMINACION)]
    assert len(tickets) == 1
    ticket = tickets[0]
    assert ticket["estado"] == "PENDIENTE"
    assert motivo in ticket["mensaje"]

    auditoria = (
        db_session.query(Auditoria)
        .filter(Auditoria.usuario_id == user_id, Auditoria.accion == "ELIMINACION_SOLICITADA")
        .first()
    )
    assert auditoria is not None, "Debe existir un registro de auditoria ELIMINACION_SOLICITADA"

    admin_usuario = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    notificaciones_admin = (
        db_session.query(Notificacion)
        .filter(
            Notificacion.usuario_id == admin_usuario.id,
            Notificacion.tipo == "SOPORTE_MENSAJE",
        )
        .all()
    )
    coincidentes = [
        n for n in notificaciones_admin
        if "Solicitud de eliminación" in n.mensaje and apellido_unico in n.mensaje
    ]
    assert len(coincidentes) == 1, f"Se esperaba 1 notificacion coincidente, se encontraron {len(coincidentes)}"


def test_solicitar_eliminacion_sin_motivo_es_valida(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, f"Org Sin Motivo {uuid.uuid4().hex[:6]}")
    _, email = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email, PASSWORD_USUARIO)

    res = client.post("/api/usuarios/me/solicitar-eliminacion", headers=headers_user, json={})
    assert res.status_code == 200, res.text

    res_mios = client.get("/api/soporte/mios", headers=headers_user)
    assert res_mios.status_code == 200, res_mios.text
    tickets = [t for t in res_mios.json() if t["mensaje"] == PREFIJO_SOLICITUD_ELIMINACION]
    assert len(tickets) == 1


def test_segunda_solicitud_pendiente_es_rechazada(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, f"Org Doble {uuid.uuid4().hex[:6]}")
    _, email = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email, PASSWORD_USUARIO)

    res1 = client.post("/api/usuarios/me/solicitar-eliminacion", headers=headers_user, json={"motivo": "Primera"})
    assert res1.status_code == 200, res1.text

    res2 = client.post("/api/usuarios/me/solicitar-eliminacion", headers=headers_user, json={"motivo": "Segunda"})
    assert res2.status_code == 409, res2.text

    res_mios = client.get("/api/soporte/mios", headers=headers_user)
    assert res_mios.status_code == 200, res_mios.text
    tickets = [t for t in res_mios.json() if t["mensaje"].startswith(PREFIJO_SOLICITUD_ELIMINACION)]
    assert len(tickets) == 1


def test_solicitar_eliminacion_motivo_muy_largo_es_rechazado(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, f"Org Largo {uuid.uuid4().hex[:6]}")
    _, email = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email, PASSWORD_USUARIO)

    res = client.post("/api/usuarios/me/solicitar-eliminacion", headers=headers_user, json={"motivo": "x" * 501})
    assert res.status_code == 422, res.text

    res_mios = client.get("/api/soporte/mios", headers=headers_user)
    assert res_mios.status_code == 200, res_mios.text
    tickets = [t for t in res_mios.json() if t["mensaje"].startswith(PREFIJO_SOLICITUD_ELIMINACION)]
    assert len(tickets) == 0


def test_super_administrador_no_puede_solicitar_eliminacion(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")

    res = client.post("/api/usuarios/me/solicitar-eliminacion", headers=headers_admin, json={"motivo": "Admin baja"})
    assert res.status_code == 403, res.text

    admin_usuario = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    tickets_admin = (
        db_session.query(TicketSoporte)
        .filter(
            TicketSoporte.usuario_id == admin_usuario.id,
            TicketSoporte.mensaje.startswith(PREFIJO_SOLICITUD_ELIMINACION),
        )
        .all()
    )
    assert len(tickets_admin) == 0
