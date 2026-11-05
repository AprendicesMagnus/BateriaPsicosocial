"""Verificación en dos pasos para roles administrativos (setting DOS_PASOS_ACTIVO)."""

import pytest

from app.core.config import get_settings


@pytest.fixture
def dos_pasos_activo(monkeypatch):
    codigos = []

    def _enviar_simulado(email, nombre, codigo):
        codigos.append(codigo)
        return True

    monkeypatch.setattr(get_settings(), "dos_pasos_activo", True)
    monkeypatch.setattr("app.services.auth.enviar_codigo_2fa", _enviar_simulado)
    return codigos


def _login_admin(client):
    return client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})


def test_admin_requiere_codigo_cuando_esta_activo(client, dos_pasos_activo):
    res = _login_admin(client)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["requiere2FA"] is True
    assert "token" not in data
    assert len(dos_pasos_activo) == 1

    res_mal = client.post(
        "/api/auth/verify-login-code",
        json={"challengeToken": data["challengeToken"], "codigo": "000000" if dos_pasos_activo[0] != "000000" else "111111"},
    )
    assert res_mal.status_code == 400

    res_ok = client.post(
        "/api/auth/verify-login-code",
        json={"challengeToken": data["challengeToken"], "codigo": dos_pasos_activo[0]},
    )
    assert res_ok.status_code == 200, res_ok.text
    assert res_ok.json()["token"]


def test_admin_entra_directo_cuando_esta_desactivado(client):
    assert get_settings().dos_pasos_activo is False
    res = _login_admin(client)
    assert res.status_code == 200, res.text
    assert res.json().get("token")
