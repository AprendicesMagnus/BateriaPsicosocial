"""crear_catalogo_productos_y_pedidos

Revision ID: c6d7e8f9a0b1
Revises: f1a2b3c4d5e6
Create Date: 2026-10-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c6d7e8f9a0b1"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "productos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("categoria", sa.String(length=40), nullable=False),
        sa.Column("precio", sa.Integer(), nullable=False),
        sa.Column("imagen_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("precio > 0", name="ck_productos_precio_positivo"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pedidos_productos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("iva", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="PENDIENTE"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pedido_producto_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("producto_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nombre_producto", sa.String(length=120), nullable=False),
        sa.Column("precio_unitario", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_productos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("cantidad > 0", name="ck_pedido_producto_items_cantidad_positiva"),
    )

    op.create_table(
        "pagos_pedidos_productos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metodo", sa.String(length=30), nullable=False),
        sa.Column("referencia", sa.String(length=100), nullable=False),
        sa.Column("monto", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="PENDIENTE"),
        sa.Column("wompi_transaction_id", sa.String(length=100), nullable=True),
        sa.Column("wompi_status", sa.String(length=30), nullable=True),
        sa.Column("wompi_payment_method", sa.String(length=80), nullable=True),
        sa.Column("banco", sa.String(length=80), nullable=True),
        sa.Column("ultimos_digitos", sa.String(length=4), nullable=True),
        sa.Column("titular", sa.String(length=150), nullable=True),
        sa.Column("mensaje_respuesta", sa.String(length=255), nullable=True),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos_productos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referencia"),
        sa.UniqueConstraint("wompi_transaction_id"),
    )

    productos = [
        ("Extintor ABC", "SST", 85000),
        ("Botiquín de primeros auxilios", "SST", 120000),
        ("Casco de seguridad", "SST", 38000),
        ("Guantes dieléctricos", "SST", 145000),
        ("Señalización de evacuación", "SST", 28000),
        ("Alarma de humo inteligente", "Tecnología", 98000),
        ("Sensor de movimiento", "Tecnología", 65000),
        ("Cámara de seguridad Wi-Fi", "Tecnología", 175000),
        ("Cerradura electrónica", "Tecnología", 420000),
        ("Sensor de inundación", "Tecnología", 72000),
    ]

    productos_table = sa.table(
        "productos",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("nombre", sa.String(120)),
        sa.column("categoria", sa.String(40)),
        sa.column("precio", sa.Integer()),
        sa.column("imagen_url", sa.String(500)),
        sa.column("activo", sa.Boolean()),
    )

    import uuid

    op.bulk_insert(
        productos_table,
        [
            {
                "id": uuid.uuid4(),
                "nombre": nombre,
                "categoria": categoria,
                "precio": precio,
                "imagen_url": "",
                "activo": True,
            }
            for nombre, categoria, precio in productos
        ],
    )


def downgrade() -> None:
    op.drop_table("pagos_pedidos_productos")
    op.drop_table("pedido_producto_items")
    op.drop_table("pedidos_productos")
    op.drop_table("productos")
