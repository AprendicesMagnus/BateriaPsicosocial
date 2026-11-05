"""Envío de correos por la API de Brevo (no se hacen llamadas reales)."""

import httpx
import pytest

from app.core.config import get_settings
from app.services import correo


class _Respuesta:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


@pytest.fixture
def brevo(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "brevo_api_key", "xkeysib-prueba")
    monkeypatch.setattr(settings, "smtp_from", "Magnus|SIG <aprendizmagnus@gmail.com>")
    llamadas = []
    estado = {"respuesta": _Respuesta(201, '{"messageId":"<x@brevo>"}')}

    def _post(url, headers=None, json=None, timeout=None):
        llamadas.append({"url": url, "headers": headers, "json": json})
        return estado["respuesta"]

    monkeypatch.setattr(correo.httpx, "post", _post)
    # Si se intentara SMTP la prueba debe fallar.
    monkeypatch.setattr(correo, "_abrir_conexion", lambda *a, **k: pytest.fail("No debe usar SMTP con Brevo"))
    return llamadas, estado


def test_codigo_2fa_se_envia_por_brevo(brevo):
    llamadas, _ = brevo
    assert correo.enviar_codigo_2fa("admin@test.com", "Ana", "123456") is True

    assert len(llamadas) == 1
    llamada = llamadas[0]
    assert llamada["url"] == correo.BREVO_URL
    assert llamada["headers"]["api-key"] == "xkeysib-prueba"
    cuerpo = llamada["json"]
    assert cuerpo["sender"] == {"name": "Magnus|SIG", "email": "aprendizmagnus@gmail.com"}
    assert cuerpo["to"] == [{"email": "admin@test.com"}]
    assert "123456" in cuerpo["textContent"]


def test_brevo_rechaza_devuelve_false(brevo):
    _, estado = brevo
    estado["respuesta"] = _Respuesta(400, '{"code":"invalid_parameter","message":"sender not valid"}')
    assert correo.enviar_correo("x@test.com", "Asunto", "Hola") is False


def test_brevo_sin_conexion_devuelve_false(brevo, monkeypatch):
    def _falla(*a, **k):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(correo.httpx, "post", _falla)
    assert correo.enviar_correo("x@test.com", "Asunto", "Hola") is False
