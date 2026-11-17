import uuid

from tests.test_soporte_mensajes import _crear_organizacion, _crear_usuario


def _headers(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _admin(client):
    return _headers(client, "admin@magnussig.com", "Admin1234")


def _nuevo_usuario(client, admin, rol="JEFE"):
    org = _crear_organizacion(client, admin, "Org Elim " + uuid.uuid4().hex[:6])
    usuario_id, email = _crear_usuario(client, admin, rol, org, "Password1234")
    return usuario_id, email


def test_admin_elimina_usuario_sin_actividad(client):
    admin = _admin(client)
    usuario_id, email = _nuevo_usuario(client, admin)
    res = client.delete(f"/api/usuarios/{usuario_id}/definitivo", headers=admin)
    assert res.status_code == 200, res.text
    assert "eliminado" in res.json()["message"]
    # Ya no existe ni puede iniciar sesión
    assert client.delete(f"/api/usuarios/{usuario_id}/definitivo", headers=admin).status_code == 404
    login = client.post("/api/auth/login", json={"email": email, "password": "Password1234"})
    assert login.status_code in (400, 401, 403, 404)


def test_no_puede_eliminarse_a_si_mismo_ni_a_un_super_admin(client):
    admin = _admin(client)
    yo = client.get("/api/auth/me", headers=admin).json()
    yo_id = (yo.get("usuario") or yo)["id"]
    res = client.delete(f"/api/usuarios/{yo_id}/definitivo", headers=admin)
    assert res.status_code == 400
    otro_id, _ = _nuevo_usuario(client, admin, "SUPER_ADMINISTRADOR")
    res = client.delete(f"/api/usuarios/{otro_id}/definitivo", headers=admin)
    assert res.status_code == 403


def test_usuario_sin_permiso_no_puede_eliminar(client):
    admin = _admin(client)
    victima_id, _ = _nuevo_usuario(client, admin)
    _, email = _nuevo_usuario(client, admin, "EVALUADOR_SST")
    res = client.delete(f"/api/usuarios/{victima_id}/definitivo", headers=_headers(client, email, "Password1234"))
    assert res.status_code == 403


def test_con_compras_se_bloquea(client, db_session):
    from app.models.commercial import Compra

    admin = _admin(client)
    usuario_id, _ = _nuevo_usuario(client, admin)
    db_session.add(
        Compra(usuario_id=uuid.UUID(str(usuario_id)), cantidad=1, tarifa_unitario=10000.0, subtotal=10000.0, iva=1900.0, total=11900.0)
    )
    db_session.commit()
    res = client.delete(f"/api/usuarios/{usuario_id}/definitivo", headers=admin)
    assert res.status_code == 409, res.text
    assert "desactivar" in res.json()["error"].lower()


def test_elimina_usuario_con_sesion_auditoria_y_mensajes(client):
    admin = _admin(client)
    usuario_id, email = _nuevo_usuario(client, admin, "EVALUADOR_SST")
    propio = _headers(client, email, "Password1234")  # genera sesión activa y auditoría de LOGIN
    res = client.post("/api/soporte", headers=propio, json={"mensaje": "Necesito ayuda con mi cuenta, por favor."})
    assert res.status_code in (200, 201), res.text
    res = client.delete(f"/api/usuarios/{usuario_id}/definitivo", headers=admin)
    assert res.status_code == 200, res.text
