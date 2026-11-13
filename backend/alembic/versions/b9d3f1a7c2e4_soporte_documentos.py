"""documentos descargables del Centro de ayuda (los sube el Super Administrador)

Revision ID: b9d3f1a7c2e4
Revises: ef31a7c9b205
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b9d3f1a7c2e4"
down_revision: Union[str, Sequence[str], None] = "ef31a7c9b205"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "soporte_documentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.String(500), nullable=True),
        sa.Column("nombre_archivo", sa.String(200), nullable=False),
        sa.Column("tipo_mime", sa.String(120), nullable=False),
        sa.Column("tamano", sa.Integer(), nullable=False),
        sa.Column("contenido", sa.LargeBinary(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("creado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("soporte_documentos")
