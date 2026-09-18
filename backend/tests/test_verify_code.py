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
