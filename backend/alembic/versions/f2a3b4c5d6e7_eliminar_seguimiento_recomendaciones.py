"""eliminar_seguimiento_recomendaciones

Revision ID: f2a3b4c5d6e7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("seguimiento_recomendaciones")


def downgrade() -> None:
    op.create_table(
        "seguimiento_recomendaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organizacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizaciones.id"), nullable=False),
        sa.Column("recomendacion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recomendaciones.id"), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="PENDIENTE"),
        sa.Column("responsable", sa.String(length=180), nullable=True),
        sa.Column("fecha_estado", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("fecha_limite", sa.Date(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organizacion_id", "recomendacion_id", name="uq_seguimiento_org_rec"),
    )
