"""
Tests de validación de código de 6 dígitos en verificación de email / reset (Etapa 4 – auditoría de validaciones).

Criterio: el código debe ser una cadena de exactamente 6 dígitos (r'^\d{6}$').
"""


def test_verificar_email_codigo_invalido_letras(client):
    res = client.post("/api/auth/verify-email", json={"email": "user@test.com", "codigo": "12345A"})
    assert res.status_code == 422


def test_verificar_email_codigo_invalido_longitud(client):
    res = client.post("/api/auth/verify-email", json={"email": "user@test.com", "codigo": "12345"})
    assert res.status_code == 422


def test_verificar_reset_codigo_invalido(client):
    res = client.post("/api/auth/verify-reset-code", json={"email": "user@test.com", "codigo": "123"})
    assert res.status_code == 422


def test_enviar_codigo_verificacion_smtp_error_no_propaga_excepcion(monkeypatch):
    from unittest.mock import patch
    from smtplib import SMTPException
    from app.core.config import get_settings
    from app.services.correo import enviar_codigo_verificacion

    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.servidor-invalido.test")

    with patch("smtplib.SMTP", side_effect=SMTPException("Error de conexión SMTP simulado")):
        resultado = enviar_codigo_verificacion("usuario@test.com", "Juan", "123456", "VERIFY_EMAIL")
        assert resultado is False
