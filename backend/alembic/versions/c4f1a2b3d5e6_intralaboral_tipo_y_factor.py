"""intralaboral dimension tipo y factor_transformacion

Revision ID: c4f1a2b3d5e6
Revises: 8a8efe933983
Create Date: 2026-09-25 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f1a2b3d5e6"
down_revision: Union[str, Sequence[str], None] = "8a8efe933983"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "dimensiones",
        sa.Column("tipo", sa.String(length=20), server_default="DIMENSION", nullable=False),
    )
    op.add_column(
        "dimensiones",
        sa.Column("factor_transformacion", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("dimensiones", "factor_transformacion")
    op.drop_column("dimensiones", "tipo")
