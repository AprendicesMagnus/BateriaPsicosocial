import uuid
from datetime import timedelta

import pytest

from app.core.crypto import hash_password, utcnow
from app.models.audit import Auditoria
from app.models.security import CodigoDosPasos, SesionActiva
from app.models.user import Rol, Usuario
from app.services import auth as auth_service

# Valor real de la configuracion, capturado al importar el modulo (antes de que
# la fixture autouse de conftest lo deje vacio en cada prueba).
ROLES_REALES = frozenset(auth_service.ROLES_REQUIEREN_2FA)

PASSWORD = "Clave12345"
ROLES_CON_2FA = ["SUPER_ADMINISTRADOR", "ADMINISTRADOR", "JEFE", "EVALUADOR_SST"]


@pytest.fixture(autouse=True)
def _limpiar_auditoria_2fa(db_session):
    """Estas pruebas dejan accesos LOGIN_2FA; otra prueba busca solo "inició sesión" en la auditoría."""
    yield
    db_session.rollback()
    db_session.query(Auditoria).filter(Auditoria.accion.in_(["LOGIN_2FA", "LOGIN_GOOGLE"])).delete(synchronize_session=False)
    db_session.commit()


@pytest.fixture
def activar_2fa(monkeypatch):
    monkeypatch.setattr(auth_service, "ROLES_REQUIEREN_2FA", set(ROLES_REALES))
    monkeypatch.setattr(auth_service.settings, "dos_pasos_activo", True)
    monkeypatch.setattr(auth_service.settings, "doble_factor_correos_exentos", "")


@pytest.fixture
def correos_2fa(monkeypatch):
    enviados = []

    def _falso(destino, nombre, codigo):
        enviados.append({"destino": destino, "codigo": codigo})
        return True

    monkeypatch.setattr(auth_service, "enviar_codigo_2fa", _falso)
    return enviados


@pytest.fixture
def crear_usuario(db_session):
    def _crear(rol_codigo):
        rol = db_session.query(Rol).filter(Rol.codigo == rol_codigo).first()
        assert rol is not None, f"El rol {rol_codigo} no esta sembrado."
        email = f"dosfa_{uuid.uuid4().hex[:10]}@test.com"
        usuario = Usuario(
            nombre="Prueba",
            apellido="DosPasos",
            email=email,
            password_hash=hash_password(PASSWORD),
            rol_id=rol.id,
            estado="ACTIVO",
            email_verificado=True,
        )
        db_session.add(usuario)
        db_session.commit()
        db_session.refresh(usuario)
        return usuario

    return _crear


def _login(client, email, **extra):
    return client.post("/api/auth/login", json={"email": email, "password": PASSWORD, **extra})


def _codigo_incorrecto(codigo):
    return "000000" if codigo != "000000" else "111111"


def test_roles_que_requieren_2fa_son_los_esperados():
    assert ROLES_REALES == {"SUPER_ADMINISTRADOR", "ADMINISTRADOR", "JEFE", "EVALUADOR_SST"}
    assert "RESPONSABLE_SST" not in ROLES_REALES


@pytest.mark.parametrize("rol", ROLES_CON_2FA)
def test_login_emite_reto_para_roles_con_2fa(client, db_session, activar_2fa, correos_2fa, crear_usuario, rol):
    usuario = crear_usuario(rol)
    res = _login(client, usuario.email)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["requiere2FA"] is True
    assert data["challengeToken"]
    assert "token" not in data
    assert len(correos_2fa) == 1
    assert correos_2fa[0]["destino"] == usuario.email
    assert len(correos_2fa[0]["codigo"]) == 6
    sesiones = db_session.query(SesionActiva).filter(SesionActiva.usuario_id == usuario.id).count()
    assert sesiones == 0


def test_responsable_sst_inicia_sesion_sin_segundo_paso(client, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("RESPONSABLE_SST")
    res = _login(client, usuario.email)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "token" in data
    assert "requiere2FA" not in data
    assert correos_2fa == []


def test_codigo_correcto_entrega_token_y_audita(client, db_session, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("JEFE")
    reto = _login(client, usuario.email).json()
    res = client.post(
        "/api/auth/verify-login-code",
        json={"challengeToken": reto["challengeToken"], "codigo": correos_2fa[0]["codigo"]},
    )
    assert res.status_code == 200, res.text
    token = res.json()["token"]
    assert res.json()["usuario"]["email"] == usuario.email

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text

    auditoria = (
        db_session.query(Auditoria)
        .filter(Auditoria.usuario_id == usuario.id, Auditoria.accion == "LOGIN_2FA")
        .count()
    )
    assert auditoria == 1


def test_codigo_incorrecto_resta_intentos(client, db_session, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("ADMINISTRADOR")
    reto = _login(client, usuario.email).json()
    malo = _codigo_incorrecto(correos_2fa[0]["codigo"])
    res = client.post(
        "/api/auth/verify-login-code",
        json={"challengeToken": reto["challengeToken"], "codigo": malo},
    )
    assert res.status_code == 400, res.text
    assert "Intentos restantes: 4" in res.json()["error"]
    registro = db_session.query(CodigoDosPasos).filter(CodigoDosPasos.usuario_id == usuario.id).one()
    assert registro.intentos == 1
    assert registro.usado is False


def test_cinco_intentos_fallidos_invalidan_el_codigo(client, db_session, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("EVALUADOR_SST")
    reto = _login(client, usuario.email).json()
    correcto = correos_2fa[0]["codigo"]
    malo = _codigo_incorrecto(correcto)
    for _ in range(5):
        res = client.post(
            "/api/auth/verify-login-code",
            json={"challengeToken": reto["challengeToken"], "codigo": malo},
        )
        assert res.status_code == 400, res.text

    db_session.expire_all()
    registro = db_session.query(CodigoDosPasos).filter(CodigoDosPasos.usuario_id == usuario.id).one()
    assert registro.usado is True

    res = client.post(
        "/api/auth/verify-login-code",
        json={"challengeToken": reto["challengeToken"], "codigo": correcto},
    )
    assert res.status_code == 400, res.text
    assert "token" not in res.json()


def test_challenge_token_no_sirve_como_sesion(client, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("SUPER_ADMINISTRADOR")
    reto = _login(client, usuario.email).json()
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {reto['challengeToken']}"})
    assert res.status_code == 401, res.text


def test_token_de_sesion_no_sirve_como_reto(client, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("RESPONSABLE_SST")
    sesion = _login(client, usuario.email).json()
    res = client.post(
        "/api/auth/verify-login-code",
        json={"challengeToken": sesion["token"], "codigo": "123456"},
    )
    assert res.status_code == 400, res.text


def test_dispositivo_confiable_salta_el_segundo_paso(client, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("JEFE")
    reto = _login(client, usuario.email).json()
    res = client.post(
        "/api/auth/verify-login-code",
        json={
            "challengeToken": reto["challengeToken"],
            "codigo": correos_2fa[0]["codigo"],
            "confiarDispositivo": True,
        },
    )
    assert res.status_code == 200, res.text
    confiable = res.json()["trustedDeviceToken"]
    assert confiable

    segundo = _login(client, usuario.email, trustedDeviceToken=confiable)
    assert segundo.status_code == 200, segundo.text
    assert "token" in segundo.json()
    assert "requiere2FA" not in segundo.json()
    assert len(correos_2fa) == 1

    otro_agente = client.post(
        "/api/auth/login",
        json={"email": usuario.email, "password": PASSWORD, "trustedDeviceToken": confiable},
        headers={"User-Agent": "otro-navegador"},
    )
    assert otro_agente.status_code == 200, otro_agente.text
    assert otro_agente.json()["requiere2FA"] is True
    assert len(correos_2fa) == 2


def test_google_cuenta_nueva_recibe_el_reto(client, activar_2fa, correos_2fa, monkeypatch):
    email = f"google_{uuid.uuid4().hex[:10]}@test.com"
    payload = {"email": email, "email_verified": True, "given_name": "Laura", "family_name": "Gomez"}
    monkeypatch.setattr(
        auth_service.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: payload,
    )
    res = client.post(
        "/api/auth/google",
        json={"credential": "x" * 30, "rol": "JEFE", "aceptaPolitica": True},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["requiere2FA"] is True
    assert "token" not in data
    assert len(correos_2fa) == 1
    assert correos_2fa[0]["destino"] == email


def test_correo_caido_responde_503_y_no_deja_codigo_vigente(client, db_session, activar_2fa, monkeypatch, crear_usuario):
    monkeypatch.setattr(auth_service, "enviar_codigo_2fa", lambda destino, nombre, codigo: False)
    usuario = crear_usuario("ADMINISTRADOR")
    res = _login(client, usuario.email)
    assert res.status_code == 503, res.text
    assert "token" not in res.json()
    vigentes = (
        db_session.query(CodigoDosPasos)
        .filter(CodigoDosPasos.usuario_id == usuario.id, CodigoDosPasos.usado.is_(False))
        .count()
    )
    assert vigentes == 0


def test_reenvio_exige_esperar_30_segundos(client, db_session, activar_2fa, correos_2fa, crear_usuario):
    usuario = crear_usuario("JEFE")
    reto = _login(client, usuario.email).json()

    inmediato = client.post("/api/auth/resend-login-code", json={"challengeToken": reto["challengeToken"]})
    assert inmediato.status_code == 429, inmediato.text
    assert len(correos_2fa) == 1

    registro = db_session.query(CodigoDosPasos).filter(CodigoDosPasos.usuario_id == usuario.id).one()
    registro.creado_en = utcnow() - timedelta(seconds=31)
    db_session.commit()

    despues = client.post("/api/auth/resend-login-code", json={"challengeToken": reto["challengeToken"]})
    assert despues.status_code == 200, despues.text
    assert len(correos_2fa) == 2
