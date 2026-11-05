import uuid

from app.core.crypto import utcnow
from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.evaluation import Notificacion

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
            "apellido": "Ocultar",
            "email": email,
            "password": password,
            "rolCodigo": rol_codigo,
            "organizacionId": organizacion_id,
        },
    )
    assert res.status_code in (200, 201), res.text
    return uuid.UUID(res.json()["id"]), email


def test_ocultar_leidas_oculta_solo_las_leidas_del_usuario(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Ocultar 1")
    id_a, email_a = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    id_b, _ = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_a = _encabezados(client, email_a, PASSWORD_USUARIO)

    notif_leida_a = Notificacion(
        usuario_id=id_a,
        tipo="RIESGO_ALTO",
        titulo="Leida A",
        mensaje="Mensaje Leida A",
        leida=True,
        fecha_envio=utcnow(),
    )
    notif_nueva_a = Notificacion(
        usuario_id=id_a,
        tipo="RIESGO_ALTO",
        titulo="Nueva A",
        mensaje="Mensaje Nueva A",
        leida=False,
        fecha_envio=utcnow(),
    )
    notif_leida_b = Notificacion(
        usuario_id=id_b,
        tipo="RIESGO_ALTO",
        titulo="Leida B",
        mensaje="Mensaje Leida B",
        leida=True,
        fecha_envio=utcnow(),
    )
    db_session.add_all([notif_leida_a, notif_nueva_a, notif_leida_b])
    db_session.commit()

    res = client.post("/api/notificaciones/ocultar-leidas", headers=headers_a)
    assert res.status_code == 200, res.text
    assert res.json().get("ocultadas") == 1

    res_lista = client.get("/api/notificaciones", headers=headers_a)
    assert res_lista.status_code == 200, res_lista.text
    titulos = [n["titulo"] for n in res_lista.json()]
    assert "Nueva A" in titulos
    assert "Leida A" not in titulos

    db_session.expire_all()
    noti_b_db = db_session.query(Notificacion).filter(Notificacion.id == notif_leida_b.id).one()
    assert noti_b_db.oculta is False


def test_ocultar_leidas_conserva_las_filas_en_la_base(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Ocultar 2")
    id_a, email_a = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_a = _encabezados(client, email_a, PASSWORD_USUARIO)

    notif_leida_a = Notificacion(
        usuario_id=id_a,
        tipo="RIESGO_ALTO",
        titulo="Leida A",
        mensaje="Mensaje Leida A",
        leida=True,
        fecha_envio=utcnow(),
    )
    db_session.add(notif_leida_a)
    db_session.commit()
    notif_id = notif_leida_a.id

    res = client.post("/api/notificaciones/ocultar-leidas", headers=headers_a)
    assert res.status_code == 200, res.text

    db_session.expire_all()
    fila = db_session.query(Notificacion).filter(Notificacion.id == notif_id).first()
    assert fila is not None
    assert fila.oculta is True
    assert fila.leida is True


def test_ocultar_leidas_sin_leidas_devuelve_cero(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Ocultar 3")
    id_a, email_a = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_a = _encabezados(client, email_a, PASSWORD_USUARIO)

    notif_nueva_a = Notificacion(
        usuario_id=id_a,
        tipo="RIESGO_ALTO",
        titulo="Nueva A",
        mensaje="Mensaje Nueva A",
        leida=False,
        fecha_envio=utcnow(),
    )
    db_session.add(notif_nueva_a)
    db_session.commit()

    res = client.post("/api/notificaciones/ocultar-leidas", headers=headers_a)
    assert res.status_code == 200, res.text
    assert res.json().get("ocultadas") == 0

    res_lista = client.get("/api/notificaciones", headers=headers_a)
    assert res_lista.status_code == 200, res_lista.text
    titulos = [n["titulo"] for n in res_lista.json()]
    assert "Nueva A" in titulos


def test_ocultar_leidas_es_idempotente(client, db_session):
    headers_admin = _encabezados(client, "admin@magnussig.com", "Admin1234")
    org_id = _crear_organizacion(client, headers_admin, "Org Ocultar 4")
    id_a, email_a = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_id, PASSWORD_USUARIO)
    headers_a = _encabezados(client, email_a, PASSWORD_USUARIO)

    notif_leida_a = Notificacion(
        usuario_id=id_a,
        tipo="RIESGO_ALTO",
        titulo="Leida A",
        mensaje="Mensaje Leida A",
        leida=True,
        fecha_envio=utcnow(),
    )
    db_session.add(notif_leida_a)
    db_session.commit()

    res1 = client.post("/api/notificaciones/ocultar-leidas", headers=headers_a)
    assert res1.status_code == 200, res1.text
    assert res1.json().get("ocultadas") == 1

    res2 = client.post("/api/notificaciones/ocultar-leidas", headers=headers_a)
    assert res2.status_code == 200, res2.text
    assert res2.json().get("ocultadas") == 0


def test_ocultar_leidas_requiere_sesion(client):
    res = client.post("/api/notificaciones/ocultar-leidas")
    assert res.status_code in (401, 403), res.text
