"""usuarios: número de resolución del responsable SST

Revision ID: a9c3e5f7b2d1
Revises: d4c27f0e9b13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a9c3e5f7b2d1"
down_revision: Union[str, Sequence[str], None] = "d4c27f0e9b13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("numero_resolucion", sa.String(length=6), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "numero_resolucion")
