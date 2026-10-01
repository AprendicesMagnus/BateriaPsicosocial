"""perfil: foto y fecha de edición; empresas: usuario creador

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("foto_url", sa.String(length=255), nullable=True))
    op.add_column(
        "usuarios",
        sa.Column("perfil_actualizado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "organizaciones",
        sa.Column("creada_por_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_organizaciones_creada_por", "organizaciones", "usuarios", ["creada_por_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_organizaciones_creada_por", "organizaciones", type_="foreignkey")
    op.drop_column("organizaciones", "creada_por_id")
    op.drop_column("usuarios", "perfil_actualizado_en")
    op.drop_column("usuarios", "foto_url")
