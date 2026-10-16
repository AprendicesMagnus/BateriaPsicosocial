"""usuarios: límite de 3 cambios de número de resolución cada 5 días

Revision ID: d2f4b6a8c0e2
Revises: c4e8a2d6f0b1
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2f4b6a8c0e2"
down_revision: Union[str, Sequence[str], None] = "c4e8a2d6f0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("resolucion_intentos", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "usuarios",
        sa.Column("resolucion_intentos_desde", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "resolucion_intentos_desde")
    op.drop_column("usuarios", "resolucion_intentos")
