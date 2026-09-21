"""
Tests de validación del campo teléfono (Etapa 4 – auditoría de validaciones).

Criterio: si se envía teléfono, debe contener entre 7 y 10 dígitos numéricos (r'^\d{7,10}$').
"""
import uuid
from app.core.nit_utils import calcular_digito_verificador_nit


def _nit_valido():
    base = f"9{str(uuid.uuid4().int)[:8]}"
    return f"{base}-{calcular_digito_verificador_nit(base)}"


def test_telefono_valido(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_org = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Org Tel Valido",
        "nit": _nit_valido(),
        "telefono": "3001234567"
    })
    assert res_org.status_code == 200


def test_telefono_invalido_letras(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_org = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Org Tel Invalido",
        "nit": _nit_valido(),
        "telefono": "300ABC4567"
    })
    assert res_org.status_code == 422


def test_telefono_invalido_corto(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_org = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Org Tel Corto",
        "nit": _nit_valido(),
        "telefono": "12345"
    })
    assert res_org.status_code == 422
