"""
Tests de validación de fortaleza de contraseña en registro y autorregistro (Etapa 4 – auditoría de validaciones).

Criterio: min 8 caracteres, al menos 1 mayúscula, 1 minúscula y 1 número.
"""


def test_registro_password_debil_sin_mayuscula(client):
    res = client.post("/api/auth/register", json={
        "nombre": "Pedro",
        "apellido": "Gómez",
        "email": "pedro@test.com",
        "password": "password123"
    })
    # Espera 400 (AppError de password_valida) o 422
    assert res.status_code in (400, 422)


def test_registro_password_debil_corta(client):
    res = client.post("/api/auth/register", json={
        "nombre": "Pedro",
        "apellido": "Gómez",
        "email": "pedro2@test.com",
        "password": "Ab1"
    })
    assert res.status_code in (400, 422)


def test_registro_password_valida(client):
    res = client.post("/api/auth/register", json={
        "nombre": "Pedro",
        "apellido": "Gómez",
        "email": "pedro3@test.com",
        "password": "Password123"
    })
    assert res.status_code == 200
