"""crear_tabla_seguimiento_recomendaciones

Revision ID: e5f6a7b8c9d0
Revises: c4f1a2b3d5e6
Create Date: 2026-09-25 17:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "c4f1a2b3d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "seguimiento_recomendaciones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organizacion_id", sa.UUID(), nullable=False),
        sa.Column("recomendacion_id", sa.UUID(), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="PENDIENTE", nullable=False),
        sa.Column("responsable", sa.String(length=180), nullable=True),
        sa.Column("fecha_estado", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"]),
        sa.ForeignKeyConstraint(["recomendacion_id"], ["recomendaciones.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organizacion_id", "recomendacion_id", name="uq_seguimiento_org_rec"),
    )


def downgrade() -> None:
    op.drop_table("seguimiento_recomendaciones")
