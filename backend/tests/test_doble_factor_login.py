import uuid
from datetime import timedelta

import pytest

from app.core.config import Settings
from app.core.crypto import utcnow
from app.core.security import crear_token_sesion
from app.models.audit import Auditoria
from app.models.security import CodigoDosPasos, DispositivoConfiable, SesionActiva
from app.models.user import Usuario
from app.services import auth as auth_service
from test_pedidos_productos import (  # noqa: F401  (helpers de las pruebas de pedidos)
    PASSWORD_USUARIO,
    _crear_organizacion,
    _crear_usuario,
)

ADMIN = {"email": "admin@magnussig.com", "password": "Admin1234"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36"


@pytest.fixture
def con_2fa(monkeypatch, db_session):
    """Activa el 2FA y captura los códigos que se enviarían por correo."""
    monkeypatch.setattr(auth_service.settings, "doble_factor_activo", True)
    monkeypatch.setattr(auth_service.settings, "doble_factor_correos_exentos", "")
    db_session.query(CodigoDosPasos).delete()
    db_session.commit()
    enviados = []
    monkeypatch.setattr(
        auth_service, "enviar_codigo_2fa", lambda destino, nombre, codigo: enviados.append((destino, codigo)) or True
    )
    return enviados


def _login(client, datos=ADMIN, ua=UA, **extra):
    return client.post("/api/auth/login", json={**datos, **extra}, headers={"User-Agent": ua.encode("latin-1")})


def _verificar(client, challenge, codigo, confiar=False, ua=UA):
    return client.post(
        "/api/auth/verify-login-code",
        json={"challengeToken": challenge, "codigo": codigo, "confiarDispositivo": confiar},
        headers={"User-Agent": ua.encode("latin-1")},
    )


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _envejecer_codigos(db_session, segundos=31):
    """Simula que pasaron `segundos` desde el último código (la espera mínima entre envíos es de 30 s)."""
    for c in db_session.query(CodigoDosPasos).all():
        c.creado_en = utcnow() - timedelta(seconds=segundos)
    db_session.commit()


def _entrar_admin(client, con_2fa, db_session):
    """Inicio de sesión completo del Super Administrador (con su código)."""
    _envejecer_codigos(db_session)
    desafio = _login(client).json()["challengeToken"]
    return _verificar(client, desafio, con_2fa[-1][1]).json()["token"]


def _usuario_sin_2fa(client, con_2fa, db_session):
    """Un Responsable SST (sin 2FA) con credenciales para iniciar sesión."""
    admin = _auth(_entrar_admin(client, con_2fa, db_session))
    org = _crear_organizacion(client, admin, f"Org 2FA {uuid.uuid4().hex[:6]}")
    _, email = _crear_usuario(client, admin, "RESPONSABLE_SST", org)
    return {"email": email, "password": PASSWORD_USUARIO}


# ---------------------------------------------------------------- verificación en dos pasos
def test_rol_con_2fa_pide_codigo_y_no_entrega_sesion(client, con_2fa):
    res = _login(client)
    assert res.status_code == 200
    data = res.json()
    assert data["requiere2FA"] is True and "token" not in data
    assert len(con_2fa) == 1 and len(con_2fa[0][1]) == 6

    # El token del reto no sirve como sesión.
    assert client.get("/api/auth/me", headers=_auth(data["challengeToken"])).status_code == 401

    ok = _verificar(client, data["challengeToken"], con_2fa[0][1])
    assert ok.status_code == 200, ok.text
    assert "metodo" not in ok.json()
    assert client.get("/api/auth/me", headers=_auth(ok.json()["token"])).status_code == 200


def test_el_codigo_se_guarda_con_hash_y_es_de_un_solo_uso(client, con_2fa, db_session):
    desafio = _login(client).json()["challengeToken"]
    codigo = con_2fa[-1][1]
    registro = db_session.query(CodigoDosPasos).order_by(CodigoDosPasos.creado_en.desc()).first()
    assert registro.codigo_hash != codigo and codigo not in registro.codigo_hash
    assert 4.5 < (registro.expira_en - utcnow()).total_seconds() / 60 <= 5.0  # vigencia de 5 minutos

    assert _verificar(client, desafio, codigo).status_code == 200
    assert _verificar(client, desafio, codigo).status_code == 400  # reutilizar el mismo código


def test_codigo_incorrecto_descuenta_intentos_y_se_bloquea(client, con_2fa):
    desafio = _login(client).json()["challengeToken"]
    correcto = con_2fa[-1][1]
    malo = "000000" if correcto != "000000" else "111111"
    for restantes in (4, 3, 2, 1, 0):
        res = _verificar(client, desafio, malo)
        assert res.status_code == 400 and f"restantes: {restantes}" in res.json()["error"]
    # Agotados los intentos, ni el código correcto sirve: hay que pedir uno nuevo.
    assert _verificar(client, desafio, correcto).status_code == 400


def test_codigo_vencido_es_rechazado(client, con_2fa, db_session):
    desafio = _login(client).json()["challengeToken"]
    registro = db_session.query(CodigoDosPasos).order_by(CodigoDosPasos.creado_en.desc()).first()
    registro.expira_en = utcnow() - timedelta(seconds=1)
    db_session.commit()
    res = _verificar(client, desafio, con_2fa[-1][1])
    assert res.status_code == 400 and "expirado" in res.json()["error"]


def test_reenviar_respeta_la_espera_e_invalida_el_codigo_anterior(client, con_2fa, db_session):
    desafio = _login(client).json()["challengeToken"]
    primero = con_2fa[-1][1]
    # Dentro de los 30 s no se puede pedir otro.
    assert client.post("/api/auth/resend-login-code", json={"challengeToken": desafio}).status_code == 429

    _envejecer_codigos(db_session)
    res = client.post("/api/auth/resend-login-code", json={"challengeToken": desafio})
    assert res.status_code == 200 and len(con_2fa) == 2
    segundo = con_2fa[-1][1]
    if primero != segundo:
        assert _verificar(client, desafio, primero).status_code == 400
    assert _verificar(client, desafio, segundo).status_code == 200


def test_roles_con_2fa_y_roles_sin_2fa(client, con_2fa, db_session):
    assert auth_service.ROLES_REQUIEREN_2FA == {"SUPER_ADMINISTRADOR", "ADMINISTRADOR", "JEFE", "EVALUADOR_SST"}
    admin = _auth(_entrar_admin(client, con_2fa, db_session))
    org = _crear_organizacion(client, admin, f"Org Roles {uuid.uuid4().hex[:6]}")
    _, email_jefe = _crear_usuario(client, admin, "JEFE", org)
    _, email_resp = _crear_usuario(client, admin, "RESPONSABLE_SST", org)

    assert _login(client, {"email": email_jefe, "password": PASSWORD_USUARIO}).json()["requiere2FA"] is True
    directo = _login(client, {"email": email_resp, "password": PASSWORD_USUARIO}).json()
    assert "token" in directo and "requiere2FA" not in directo


def test_solo_el_correo_exento_entra_sin_codigo(client, con_2fa, db_session, monkeypatch):
    # El admin de pruebas (exento por defecto) entra directo, aunque el 2FA esté activo.
    monkeypatch.setattr(auth_service.settings, "doble_factor_correos_exentos", "Admin@MagnusSIG.com ")
    directo = _login(client).json()
    assert "token" in directo and "requiere2FA" not in directo and con_2fa == []

    # Cualquier otro usuario con rol obligado sigue pidiendo código.
    admin = _auth(directo["token"])
    org = _crear_organizacion(client, admin, f"Org Exenta {uuid.uuid4().hex[:6]}")
    _, email_jefe = _crear_usuario(client, admin, "JEFE", org)
    assert _login(client, {"email": email_jefe, "password": PASSWORD_USUARIO}).json()["requiere2FA"] is True

    # Si se vacía la lista, el admin vuelve a pedir código.
    monkeypatch.setattr(auth_service.settings, "doble_factor_correos_exentos", "")
    assert _login(client).json()["requiere2FA"] is True


def test_apagado_global_no_pide_codigo(client, con_2fa, monkeypatch):
    monkeypatch.setattr(auth_service.settings, "doble_factor_activo", False)
    assert "token" in _login(client).json()


def test_google_tambien_pide_codigo_y_se_audita_como_google(client, con_2fa, monkeypatch, db_session):
    monkeypatch.setattr(
        "app.services.auth.google_id_token.verify_oauth2_token",
        lambda *a, **k: {"email": ADMIN["email"], "email_verified": True, "given_name": "A", "family_name": "B"},
    )
    res = client.post("/api/auth/google", json={"credential": "x" * 30}, headers={"User-Agent": UA})
    assert res.status_code == 200 and res.json()["requiere2FA"] is True and "token" not in res.json()

    ok = _verificar(client, res.json()["challengeToken"], con_2fa[-1][1])
    assert ok.status_code == 200 and "token" in ok.json()
    admin = db_session.query(Usuario).filter(Usuario.email == ADMIN["email"]).one()
    ultimo = (
        db_session.query(Auditoria).filter(Auditoria.usuario_id == admin.id).order_by(Auditoria.registrado_en.desc()).first()
    )
    assert ultimo.accion == "LOGIN_GOOGLE"
    # No dejar el registro: otras pruebas buscan solo "inició sesión".
    db_session.query(Auditoria).filter(Auditoria.accion == "LOGIN_GOOGLE").delete()
    db_session.commit()


def test_login_con_codigo_queda_auditado_como_login(client, con_2fa, db_session):
    _entrar_admin(client, con_2fa, db_session)
    admin = db_session.query(Usuario).filter(Usuario.email == ADMIN["email"]).one()
    ultimo = (
        db_session.query(Auditoria).filter(Auditoria.usuario_id == admin.id).order_by(Auditoria.registrado_en.desc()).first()
    )
    assert ultimo.accion == "LOGIN"  # así "Último acceso" del Panel sigue funcionando


# ---------------------------------------------------------------- dispositivo de confianza
def test_dispositivo_de_confianza_dura_4_horas_y_se_vincula_al_navegador(client, con_2fa, db_session):
    desafio = _login(client).json()["challengeToken"]
    ok = _verificar(client, desafio, con_2fa[-1][1], confiar=True).json()
    token = ok["trustedDeviceToken"]
    registro = db_session.query(DispositivoConfiable).order_by(DispositivoConfiable.creado_en.desc()).first()
    assert registro.token_hash != token
    assert 3.9 < (registro.expira_en - utcnow()).total_seconds() / 3600 <= 4.0

    _envejecer_codigos(db_session)
    enviados = len(con_2fa)
    assert "token" in _login(client, trustedDeviceToken=token).json()  # sin código
    assert len(con_2fa) == enviados

    # Otro navegador / sin el token: vuelve a pedir el código.
    assert _login(client, ua="Otro navegador", trustedDeviceToken=token).json()["requiere2FA"] is True
    _envejecer_codigos(db_session)
    assert _login(client).json()["requiere2FA"] is True

    # Vencido: vuelve a pedirlo.
    registro.expira_en = utcnow() - timedelta(minutes=1)
    db_session.commit()
    _envejecer_codigos(db_session)
    assert _login(client, trustedDeviceToken=token).json()["requiere2FA"] is True


def test_sin_marcar_confiar_no_se_entrega_token_de_dispositivo(client, con_2fa):
    desafio = _login(client).json()["challengeToken"]
    assert "trustedDeviceToken" not in _verificar(client, desafio, con_2fa[-1][1]).json()


def test_revocar_dispositivos_de_confianza(client, con_2fa, db_session):
    desafio = _login(client).json()["challengeToken"]
    ok = _verificar(client, desafio, con_2fa[-1][1], confiar=True).json()
    res = client.delete("/api/auth/trusted-devices", headers=_auth(ok["token"]))
    assert res.status_code == 200 and res.json()["revocados"] >= 1
    _envejecer_codigos(db_session)
    assert _login(client, trustedDeviceToken=ok["trustedDeviceToken"]).json()["requiere2FA"] is True


def test_token_de_dispositivo_de_otro_usuario_no_sirve(client, con_2fa, db_session):
    desafio = _login(client).json()["challengeToken"]
    token_admin = _verificar(client, desafio, con_2fa[-1][1], confiar=True).json()["trustedDeviceToken"]
    admin = _auth(_entrar_admin(client, con_2fa, db_session))
    org = _crear_organizacion(client, admin, f"Org Jefe {uuid.uuid4().hex[:6]}")
    _, email = _crear_usuario(client, admin, "JEFE", org)
    res = _login(client, {"email": email, "password": PASSWORD_USUARIO}, trustedDeviceToken=token_admin)
    assert res.json()["requiere2FA"] is True


def test_user_agent_con_caracteres_no_ascii_no_rompe_el_dispositivo_de_confianza(client, con_2fa, db_session):
    ua = "Navegador-Ñandú/1.0"
    desafio = _login(client, ua=ua).json()["challengeToken"]
    token = _verificar(client, desafio, con_2fa[-1][1], confiar=True, ua=ua).json()["trustedDeviceToken"]
    _envejecer_codigos(db_session)
    res = _login(client, ua=ua, trustedDeviceToken=token)
    assert res.status_code == 200 and "token" in res.json()


# ---------------------------------------------------------------- sesiones activas
def test_sesiones_listar_marcar_actual_y_cerrar_una(client, con_2fa, db_session):
    datos = _usuario_sin_2fa(client, con_2fa, db_session)
    a = _login(client, datos).json()["token"]
    b = _login(client, datos).json()["token"]
    lista = client.get("/api/auth/sessions", headers=_auth(a)).json()
    assert len(lista) == 2 and [s["actual"] for s in lista].count(True) == 1
    id_b = next(s["id"] for s in lista if not s["actual"])

    assert client.delete(f"/api/auth/sessions/{id_b}", headers=_auth(a)).status_code == 200
    assert client.get("/api/auth/me", headers=_auth(b)).status_code == 401  # B perdió el acceso
    assert client.get("/api/auth/me", headers=_auth(a)).status_code == 200  # A sigue


def test_no_se_pueden_cerrar_sesiones_ajenas(client, con_2fa, db_session):
    a = _login(client, _usuario_sin_2fa(client, con_2fa, db_session)).json()["token"]
    b = _login(client, _usuario_sin_2fa(client, con_2fa, db_session)).json()["token"]
    id_de_b = client.get("/api/auth/sessions", headers=_auth(b)).json()[0]["id"]
    assert id_de_b not in [s["id"] for s in client.get("/api/auth/sessions", headers=_auth(a)).json()]
    client.delete(f"/api/auth/sessions/{id_de_b}", headers=_auth(a))
    assert client.get("/api/auth/me", headers=_auth(b)).status_code == 200  # la de B sigue abierta


def test_cerrar_las_demas_conserva_la_actual(client, con_2fa, db_session):
    datos = _usuario_sin_2fa(client, con_2fa, db_session)
    tokens = [_login(client, datos).json()["token"] for _ in range(3)]
    res = client.post("/api/auth/sessions/close-others", headers=_auth(tokens[0]))
    assert res.json()["cerradas"] == 2
    assert client.get("/api/auth/me", headers=_auth(tokens[0])).status_code == 200
    assert all(client.get("/api/auth/me", headers=_auth(t)).status_code == 401 for t in tokens[1:])


def test_logout_revoca_la_sesion_actual(client, con_2fa, db_session):
    token = _login(client, _usuario_sin_2fa(client, con_2fa, db_session)).json()["token"]
    assert client.post("/api/auth/logout", headers=_auth(token)).status_code == 200
    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 401


def test_token_anterior_sin_sesion_sigue_funcionando(client, db_session):
    admin = db_session.query(Usuario).filter(Usuario.email == ADMIN["email"]).one()
    legado = crear_token_sesion(str(admin.id), "SUPER_ADMINISTRADOR", admin.email)  # sin id de sesión
    assert client.get("/api/auth/me", headers=_auth(legado)).status_code == 200


def test_sesion_vencida_en_base_de_datos_es_rechazada(client, con_2fa, db_session):
    token = _login(client, _usuario_sin_2fa(client, con_2fa, db_session)).json()["token"]
    sesion = db_session.query(SesionActiva).order_by(SesionActiva.creado_en.desc()).first()
    sesion.expiracion = utcnow() - timedelta(seconds=1)
    db_session.commit()
    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 401


# ---------------------------------------------------------------- configuración
def _produccion(**extra):
    return Settings(
        _env_file=None,
        env="production",
        database_url="postgresql://u:p@localhost/db",
        jwt_secret="x" * 40,
        encryption_key="k",
        admin_password="Admin1234",
        wompi_public_key="a", wompi_private_key="b", wompi_integrity_secret="c", wompi_events_secret="d",
        **extra,
    )


def test_en_produccion_con_2fa_exige_correo_configurado():
    with pytest.raises(ValueError, match="SMTP_HOST"):
        _produccion(doble_factor_activo=True, smtp_host="")
    assert _produccion(doble_factor_activo=True, smtp_host="smtp.gmail.com").doble_factor_activo is True
    assert _produccion(doble_factor_activo=False, smtp_host="").doble_factor_activo is False
