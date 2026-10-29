import uuid

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


def _obtener_notificaciones_soporte(client, headers):
    res = client.get("/api/notificaciones", headers=headers)
    assert res.status_code == 200, res.text
    return [n for n in res.json() if n["tipo"] == "SOPORTE_RESPUESTA"]


def test_admin_responde_ticket_notifica_autor(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Notif 1")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    notis_iniciales = _obtener_notificaciones_soporte(client, headers_user)
    assert len(notis_iniciales) == 0

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_user,
        json={"mensaje": "Consulta sobre informe de bateria."},
    )
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    res_resp = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "El informe ya esta disponible para descarga."},
    )
    assert res_resp.status_code == 200, res_resp.text

    notis = _obtener_notificaciones_soporte(client, headers_user)
    assert len(notis) == 1
    noti = notis[0]
    assert noti["leida"] is False
    assert noti["titulo"] == "Respondieron tu mensaje del Centro de ayuda"
    assert noti["mensaje"] == (
        "Respuesta: El informe ya esta disponible "
        "para descarga."
    )
    assert noti["evaluacionId"] is None


def test_admin_responde_propio_ticket_no_notifica(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")

    notis_antes = len(_obtener_notificaciones_soporte(client, headers_admin))

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_admin,
        json={"mensaje": "Ticket generado por super administrador."},
    )
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    res_resp = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "Respuesta interna del administrador a su propio ticket."},
    )
    assert res_resp.status_code == 200, res_resp.text

    notis_despues = len(_obtener_notificaciones_soporte(client, headers_admin))
    assert notis_despues == notis_antes


def test_respuesta_vacia_no_crea_notificacion(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Notif 3")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_user,
        json={"mensaje": "Duda para validar respuesta vacia."},
    )
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    notis_antes = len(_obtener_notificaciones_soporte(client, headers_user))

    # Error de validacion con respuesta vacia
    res_vacia = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": ""},
    )
    assert res_vacia.status_code in (400, 422)

    notis_despues = len(_obtener_notificaciones_soporte(client, headers_user))
    assert notis_despues == notis_antes


def test_marcar_resuelto_no_crea_notificacion(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Notif 4")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_user,
        json={"mensaje": "Ticket que sera marcado como resuelto sin respuesta."},
    )
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    notis_antes = len(_obtener_notificaciones_soporte(client, headers_user))

    res_resolver = client.post(
        f"/api/soporte/{ticket_id}/resolver",
        headers=headers_admin,
    )
    assert res_resolver.status_code == 200, res_resolver.text
    assert res_resolver.json()["estado"] == "RESUELTO"

    notis_despues = len(_obtener_notificaciones_soporte(client, headers_user))
    assert notis_despues == notis_antes


def test_tercer_usuario_no_recibe_notificacion(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Notif 5")
    _, email_user1 = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    _, email_user2 = _crear_usuario(client, headers_admin, "JEFE", org_id, PASSWORD_USUARIO)

    headers_user1 = _encabezados(client, email_user1, PASSWORD_USUARIO)
    headers_user2 = _encabezados(client, email_user2, PASSWORD_USUARIO)

    notis_antes_u2 = len(_obtener_notificaciones_soporte(client, headers_user2))

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_user1,
        json={"mensaje": "Mensaje de usuario 1."},
    )
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    res_resp = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "Respuesta dirigida al usuario 1."},
    )
    assert res_resp.status_code == 200, res_resp.text

    notis_despues_u2 = len(_obtener_notificaciones_soporte(client, headers_user2))
    assert notis_despues_u2 == notis_antes_u2


def test_admin_responde_dos_veces_mismo_ticket(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Notif 6")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    notis_antes = len(_obtener_notificaciones_soporte(client, headers_user))

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_user,
        json={"mensaje": "Pregunta que recibira dos respuestas."},
    )
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    # Primera respuesta
    res1 = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "Primera respuesta preliminar."},
    )
    assert res1.status_code == 200, res1.text

    # Segunda respuesta
    res2 = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "Segunda respuesta definitiva y corregida."},
    )
    assert res2.status_code == 200, res2.text
    assert res2.json()["respuesta"] == "Segunda respuesta definitiva y corregida."

    notis = _obtener_notificaciones_soporte(client, headers_user)
    assert len(notis) - notis_antes == 2

    # Verificar que en /api/soporte/mios queda la ultima respuesta guardada
    res_mios = client.get("/api/soporte/mios", headers=headers_user)
    assert res_mios.status_code == 200, res_mios.text
    ticket_en_mios = next(t for t in res_mios.json() if t["id"] == ticket_id)
    assert ticket_en_mios["respuesta"] == "Segunda respuesta definitiva y corregida."


def test_respuesta_solo_espacios_responde_400_y_no_notifica(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Notif 7")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_user,
        json={"mensaje": "Mensaje para validar respuesta con solo espacios."},
    )
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    notis_antes = len(_obtener_notificaciones_soporte(client, headers_user))

    # Solo espacios debe responder 400
    res_espacios = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "   "},
    )
    assert res_espacios.status_code == 400, f"Se esperaba 400, fue {res_espacios.status_code}"

    # Solo saltos de linea y tabulaciones tambien debe responder 400
    res_tabs = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "\n\t "},
    )
    assert res_tabs.status_code == 400, f"Se esperaba 400, fue {res_tabs.status_code}"

    # No se debe haber creado ninguna notificacion SOPORTE_RESPUESTA
    notis_despues = len(_obtener_notificaciones_soporte(client, headers_user))
    assert notis_despues == notis_antes, "Respuesta con solo espacios no debe generar notificacion"

    # El ticket no debe haber quedado con respuesta ni en estado RESUELTO
    res_mios = client.get("/api/soporte/mios", headers=headers_user)
    assert res_mios.status_code == 200, res_mios.text
    ticket_en_mios = next(t for t in res_mios.json() if t["id"] == ticket_id)
    assert ticket_en_mios["respuesta"] is None, "El ticket no debe tener respuesta tras rechazar solo espacios"
    assert ticket_en_mios["estado"] != "RESUELTO", "El ticket no debe quedar RESUELTO tras rechazar solo espacios"


def _obtener_notificaciones_por_tipo(client, headers, tipo):
    res = client.get("/api/notificaciones", headers=headers)
    assert res.status_code == 200, res.text
    return [n for n in res.json() if n["tipo"] == tipo]


def test_usuario_crea_ticket_notifica_a_super_administrador(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Mensaje 1")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)
    texto = "Consulta sobre informe de bateria para el aviso al administrador."
    esperado = f"Prueba Soporte: {texto}"

    antes = [n for n in _obtener_notificaciones_por_tipo(client, headers_admin, "SOPORTE_MENSAJE") if n["mensaje"] == esperado]
    assert len(antes) == 0

    res_ticket = client.post("/api/soporte", headers=headers_user, json={"mensaje": texto})
    assert res_ticket.status_code == 200, res_ticket.text

    despues = [n for n in _obtener_notificaciones_por_tipo(client, headers_admin, "SOPORTE_MENSAJE") if n["mensaje"] == esperado]
    assert len(despues) == 1
    assert despues[0]["titulo"] == "Nuevo mensaje en el Centro de ayuda"
    assert despues[0]["leida"] is False


def test_super_admin_crea_ticket_propio_no_se_avisa_a_si_mismo(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    antes = len(_obtener_notificaciones_por_tipo(client, headers_admin, "SOPORTE_MENSAJE"))

    res_ticket = client.post(
        "/api/soporte",
        headers=headers_admin,
        json={"mensaje": "Mensaje propio del super administrador sin aviso a si mismo."},
    )
    assert res_ticket.status_code == 200, res_ticket.text

    despues = len(_obtener_notificaciones_por_tipo(client, headers_admin, "SOPORTE_MENSAJE"))
    assert despues == antes


def test_mensaje_largo_se_recorta_a_140_caracteres_en_el_aviso(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Mensaje 3")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)
    esperado = "Prueba Soporte: " + "A" * 140 + "…"

    res_ticket = client.post("/api/soporte", headers=headers_user, json={"mensaje": "A" * 200})
    assert res_ticket.status_code == 200, res_ticket.text

    coinciden = [n for n in _obtener_notificaciones_por_tipo(client, headers_admin, "SOPORTE_MENSAJE") if n["mensaje"] == esperado]
    assert len(coinciden) == 1


def test_respuesta_larga_se_recorta_a_140_caracteres_en_el_aviso(client):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Soporte Respuesta 4")
    _, email_user = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_user = _encabezados(client, email_user, PASSWORD_USUARIO)

    res_ticket = client.post("/api/soporte", headers=headers_user, json={"mensaje": "Consulta para respuesta larga."})
    assert res_ticket.status_code == 200, res_ticket.text
    ticket_id = res_ticket.json()["id"]

    res_resp = client.post(
        f"/api/soporte/{ticket_id}/responder",
        headers=headers_admin,
        json={"respuesta": "B" * 200},
    )
    assert res_resp.status_code == 200, res_resp.text

    notis = _obtener_notificaciones_soporte(client, headers_user)
    assert len(notis) == 1
    assert notis[0]["mensaje"] == "Respuesta: " + "B" * 140 + "…"
