"""usuarios: verificación del número de resolución (la marca el Super Administrador)

Revision ID: c4e8a2d6f0b1
Revises: 82080c5be0fb
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8a2d6f0b1"
down_revision: Union[str, Sequence[str], None] = "82080c5be0fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("resolucion_verificada", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "resolucion_verificada")
