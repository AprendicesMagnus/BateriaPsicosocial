"""
Tests de validación de cantidad en CompraCreate (Etapa 4 – auditoría de validaciones).

Criterio: cantidad debe ser un entero > 0 (gt=0).
"""


def test_compra_cantidad_invalida_cero(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    res_compra = client.post("/api/compras", headers=headers, json={"cantidad": 0})
    assert res_compra.status_code == 422


def test_compra_cantidad_invalida_negativa(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    res_compra = client.post("/api/compras", headers=headers, json={"cantidad": -5})
    assert res_compra.status_code == 422


def test_compra_cantidad_valida(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    res_compra = client.post("/api/compras", headers=headers, json={"cantidad": 3})
    assert res_compra.status_code == 200
    assert res_compra.json()["cantidad"] == 3
