"""
Tests de validación del campo teléfono (Etapa 4 – auditoría de validaciones).

Criterio: si se envía teléfono, debe contener entre 7 y 10 dígitos numéricos (r'^\d{7,10}$').
"""
import uuid


def test_telefono_valido(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    nit = f"9{str(uuid.uuid4().int)[:8]}"
    res_org = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Org Tel Valido",
        "nit": nit,
        "telefono": "3001234567"
    })
    assert res_org.status_code == 200


def test_telefono_invalido_letras(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    nit = f"9{str(uuid.uuid4().int)[:8]}"
    res_org = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Org Tel Invalido",
        "nit": nit,
        "telefono": "300ABC4567"
    })
    assert res_org.status_code == 422


def test_telefono_invalido_corto(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    nit = f"9{str(uuid.uuid4().int)[:8]}"
    res_org = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Org Tel Corto",
        "nit": nit,
        "telefono": "12345"
    })
    assert res_org.status_code == 422
