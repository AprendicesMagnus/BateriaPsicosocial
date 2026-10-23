import uuid
import pytest

from app.core.nit_utils import calcular_digito_verificador_nit

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


def _crear_usuario(client, headers_admin, rol_codigo, organizacion_id, password):
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


def test_usuario_crea_ticket_y_aislamiento(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Test 1")
    _, email_user1 = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    _, email_user2 = _crear_usuario(client, headers_admin, "JEFE", org_id, PASSWORD_USUARIO)

    headers_user1 = _encabezados(client, email_user1, PASSWORD_USUARIO)
    headers_user2 = _encabezados(client, email_user2, PASSWORD_USUARIO)

    # (a) un usuario crea un ticket con POST /api/soporte y lo ve en GET /api/soporte/mios con respuesta None
    res_crear = client.post("/api/soporte", headers=headers_user1, json={"mensaje": "Hola, necesito ayuda con mi cuenta."})
    assert res_crear.status_code == 200, res_crear.text
    ticket_id = res_crear.json()["id"]

    res_mios1 = client.get("/api/soporte/mios", headers=headers_user1)
    assert res_mios1.status_code == 200, res_mios1.text
    tickets1 = res_mios1.json()
    assert any(t["id"] == ticket_id for t in tickets1)
    ticket_creado = next(t for t in tickets1 if t["id"] == ticket_id)
    assert ticket_creado["mensaje"] == "Hola, necesito ayuda con mi cuenta."
    assert ticket_creado["respuesta"] is None
    assert ticket_creado["respondidoEn"] is None
    assert ticket_creado["estado"] == "PENDIENTE"

    # (b) otro usuario no ve ese ticket en su GET /api/soporte/mios
    res_mios2 = client.get("/api/soporte/mios", headers=headers_user2)
    assert res_mios2.status_code == 200, res_mios2.text
    tickets2 = res_mios2.json()
    assert not any(t["id"] == ticket_id for t in tickets2)


def test_admin_responde_ticket(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Test 2")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    res_crear = client.post("/api/soporte", headers=headers_user, json={"mensaje": "Tengo una duda con los reportes."})
    assert res_crear.status_code == 200, res_crear.text
    ticket_id = res_crear.json()["id"]

    # (c) el super administrador responde con POST /api/soporte/{id}/responder y el usuario ve la respuesta, respondidoEn y estado RESUELTO
    res_resp = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "Hemos revisado tu caso y ya fue solucionado."},
    )
    assert res_resp.status_code == 200, res_resp.text
    data_resp = res_resp.json()
    assert data_resp["respuesta"] == "Hemos revisado tu caso y ya fue solucionado."
    assert data_resp["respondidoEn"] is not None
    assert data_resp["estado"] == "RESUELTO"

    res_mios = client.get("/api/soporte/mios", headers=headers_user)
    assert res_mios.status_code == 200, res_mios.text
    ticket_user = next(t for t in res_mios.json() if t["id"] == ticket_id)
    assert ticket_user["respuesta"] == "Hemos revisado tu caso y ya fue solucionado."
    assert ticket_user["respondidoEn"] is not None
    assert ticket_user["estado"] == "RESUELTO"


def test_no_admin_responder_ticket_retorna_403(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Test 3")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    res_crear = client.post("/api/soporte", headers=headers_user, json={"mensaje": "Pregunta de soporte."})
    assert res_crear.status_code == 200, res_crear.text
    ticket_id = res_crear.json()["id"]

    # (d) un usuario no administrador recibe 403 en POST /api/soporte/{id}/responder
    res_resp = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_user,
        json={"respuesta": "Intento de respuesta no autorizada."},
    )
    assert res_resp.status_code == 403, res_resp.text


def test_respuesta_vacia_retorna_422(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Test 4")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    res_crear = client.post("/api/soporte", headers=headers_user, json={"mensaje": "Pregunta de validacion."})
    assert res_crear.status_code == 200, res_crear.text
    ticket_id = res_crear.json()["id"]

    # (e) una respuesta vacia devuelve 422
    res_vacia = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": ""},
    )
    assert res_vacia.status_code == 422, res_vacia.text
