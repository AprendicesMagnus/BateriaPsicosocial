"""planes de baterías (informativos, administrables desde el panel)

Revision ID: b7d1f3a9c5e2
Revises: a9c3e5f7b2d1
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b7d1f3a9c5e2"
down_revision: Union[str, Sequence[str], None] = "a9c3e5f7b2d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Precios de ejemplo (COP por batería): el administrador los cambia desde el Panel.
PLANES_INICIALES = [
    ("Plan 1 a 5", 1, 5, 45000),
    ("Plan 6 a 10", 6, 10, 42000),
    ("Plan 11 a 20", 11, 20, 39000),
    ("Plan 21 a 30", 21, 30, 36000),
    ("Plan 31 a 50", 31, 50, 33000),
    ("Plan 51 a 100", 51, 100, 30000),
    ("Plan 101 en adelante", 101, None, 27000),
]


def upgrade() -> None:
    tabla = op.create_table(
        "planes_baterias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("cantidad_min", sa.Integer(), nullable=False),
        sa.Column("cantidad_max", sa.Integer(), nullable=True),
        sa.Column("precio_unitario", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.bulk_insert(
        tabla,
        [
            {"id": uuid.uuid4(), "nombre": n, "cantidad_min": mn, "cantidad_max": mx, "precio_unitario": p, "activo": True}
            for n, mn, mx, p in PLANES_INICIALES
        ],
    )


def downgrade() -> None:
    op.drop_table("planes_baterias")
