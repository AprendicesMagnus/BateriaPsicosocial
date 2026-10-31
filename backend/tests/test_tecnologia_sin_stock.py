import uuid

from test_pedidos_productos import (  # noqa: F401
    PREFIJO_PRODUCTO,
    _bloquear_wompi_red,
    _headers_admin,
    _limpiar_datos,
)

from app.models.product import Producto


def _producto(client, headers, categoria, stock, es_servicio=False):
    res = client.post(
        "/api/productos",
        headers=headers,
        json={
            "nombre": f"{PREFIJO_PRODUCTO} Sin stock {uuid.uuid4().hex[:6]}",
            "categoria": categoria,
            "precio": 50000,
            "imagen_url": "",
            "stock": stock,
            "es_servicio": es_servicio,
        },
    )
    assert res.status_code in (200, 201), res.text
    return res.json()


def _pedir(client, headers, producto, cantidad):
    return client.post(
        "/api/pedidos-productos",
        headers=headers,
        json={"items": [{"producto_id": producto["id"], "cantidad": cantidad}]},
    )


def test_servicio_no_maneja_stock_ni_aparece_agotado(client):
    headers = _headers_admin(client)
    # Mismo criterio en cualquier categoría (SST con asesorías, Tecnología, etc.).
    for categoria in ("SST", "Tecnología"):
        prod = _producto(client, headers, categoria, 0, es_servicio=True)
        assert prod["es_servicio"] is True
        assert prod["maneja_stock"] is False
        assert prod["agotado"] is False
        assert prod["stock_bajo"] is False


def test_producto_normal_de_tecnologia_si_maneja_stock(client):
    headers = _headers_admin(client)
    prod = _producto(client, headers, "Tecnología", 0)
    assert prod["maneja_stock"] is True and prod["agotado"] is True


def test_cambiar_a_servicio_desde_edicion(client):
    headers = _headers_admin(client)
    prod = _producto(client, headers, "SST", 0)
    assert prod["agotado"] is True
    res = client.patch(f"/api/productos/{prod['id']}", headers=headers, json={"es_servicio": True})
    assert res.status_code == 200, res.text
    assert res.json()["agotado"] is False and res.json()["maneja_stock"] is False


def test_tecnologia_permite_pedir_sin_stock_y_no_lo_modifica(client, db_session):
    headers = _headers_admin(client)
    prod = _producto(client, headers, "SST", 0, es_servicio=True)

    res = _pedir(client, headers, prod, 3)
    assert res.status_code == 200, res.text
    pedido_id = res.json()["id"]
    assert db_session.get(Producto, uuid.UUID(prod["id"])).stock == 0

    res = client.post(f"/api/pedidos-productos/{pedido_id}/cancelar", headers=headers)
    assert res.status_code == 200, res.text
    db_session.expire_all()
    assert db_session.get(Producto, uuid.UUID(prod["id"])).stock == 0


def test_otras_categorias_siguen_validando_stock(client, db_session):
    headers = _headers_admin(client)
    prod = _producto(client, headers, "Electrónicos", 1)
    assert prod["maneja_stock"] is True

    assert _pedir(client, headers, prod, 2).status_code == 409

    res = _pedir(client, headers, prod, 1)
    assert res.status_code == 200, res.text
    assert db_session.get(Producto, uuid.UUID(prod["id"])).stock == 0
