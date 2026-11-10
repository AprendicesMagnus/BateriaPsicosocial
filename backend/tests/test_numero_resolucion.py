import uuid

import pytest

from app.models.user import Usuario


def _registro(client, resolucion, rol="EVALUADOR_SST"):
    cuerpo = {
        "nombre": "Prueba",
        "apellido": "Resolucion",
        "email": f"res_{uuid.uuid4().hex[:10]}@example.com",
        "password": "Clave1234",
        "rol": rol,
        "aceptaPolitica": True,
    }
    if resolucion is not None:
        cuerpo["numeroResolucion"] = resolucion
    return client.post("/api/auth/register", json=cuerpo), cuerpo["email"]


@pytest.mark.parametrize("numero", ["123", "1234", "12345", "123456", "000"])
def test_psicologo_acepta_resolucion_de_3_a_6_digitos(client, db_session, numero):
    res, email = _registro(client, numero)
    assert res.status_code in (200, 201), res.text
    usuario = db_session.query(Usuario).filter(Usuario.email == email).one()
    assert usuario.numero_resolucion == numero


@pytest.mark.parametrize("numero", ["", "1", "12", "1234567", "12a456", "12 34", "-123"])
def test_psicologo_rechaza_resolucion_fuera_de_rango(client, numero):
    res, _ = _registro(client, numero)
    assert res.status_code in (400, 422), res.text


def test_psicologo_sin_resolucion_es_rechazado(client):
    res, _ = _registro(client, None)
    assert res.status_code == 400
    assert "entre 3 y 6" in res.json()["error"]
