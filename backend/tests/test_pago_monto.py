"""
Tests de validación de monto en PagoCreate y servicio procesar_pago (Etapa 3 – auditoría de validaciones).

Criterios:
1. Pydantic schema: `monto` debe ser > 0 (gt=0). Si se pasa <= 0, retorna HTTP 422.
2. Capa de servicio: Si `monto` no coincide con `compra.total`, retorna HTTP 400 con AppError.
3. Caso feliz: Si `monto` coincide con `compra.total`, procesa el pago exitosamente (HTTP 200).
"""
import uuid


def test_pago_monto_negativo_o_cero(client):
    """Verifica que Pydantic rechace montos <= 0 con HTTP 422."""
    # Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    # Intentar enviar pago con monto <= 0
    res_pago = client.post(
        "/api/pagos",
        headers=headers,
        json={"compraId": str(uuid.uuid4()), "metodo": "tarjeta", "monto": -10.0},
    )
    assert res_pago.status_code == 422

    res_pago_zero = client.post(
        "/api/pagos",
        headers=headers,
        json={"compraId": str(uuid.uuid4()), "metodo": "tarjeta", "monto": 0},
    )
    assert res_pago_zero.status_code == 422


def test_pago_monto_no_coincide_con_total(client):
    """Verifica que el servicio rechace pagos donde monto != compra.total con HTTP 400."""
    # Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    # 1. Crear compra de 1 batería (subtotal 10000 + IVA 19% = 11900)
    res_compra = client.post(
        "/api/compras",
        headers=headers,
        json={"cantidad": 1, "bateriaNombre": "Batería Test"},
    )
    assert res_compra.status_code == 200
    compra_data = res_compra.json()
    compra_id = compra_data["id"]
    total_real = compra_data["total"]  # 11900.0

    # 2. Enviar pago con monto incorrecto (9000.0)
    res_pago = client.post(
        "/api/pagos",
        headers=headers,
        json={"compraId": compra_id, "metodo": "tarjeta", "monto": 9000.0},
    )
    assert res_pago.status_code == 400
    assert "no coincide" in res_pago.json().get("detail", "").lower() or "error" in res_pago.json()


def test_pago_monto_correcto_exitoso(client):
    """Verifica que el servicio procese el pago correctamente cuando el monto coincide."""
    # Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    # 1. Crear compra
    res_compra = client.post(
        "/api/compras",
        headers=headers,
        json={"cantidad": 2, "bateriaNombre": "Batería Test"},
    )
    assert res_compra.status_code == 200
    compra_data = res_compra.json()
    compra_id = compra_data["id"]
    total_real = compra_data["total"]

    # 2. Enviar pago con monto exacto
    res_pago = client.post(
        "/api/pagos",
        headers=headers,
        json={"compraId": compra_id, "metodo": "tarjeta", "monto": total_real},
    )
    assert res_pago.status_code == 200
    assert res_pago.json()["compraEstado"] == "PAGADA"
