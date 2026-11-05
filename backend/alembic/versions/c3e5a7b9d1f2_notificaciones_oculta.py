"""notificaciones: columna oculta (quitar de la lista las ya leidas sin borrar el registro)

Revision ID: c3e5a7b9d1f2
Revises: e9a2b3c4d5f6
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3e5a7b9d1f2"
down_revision: Union[str, Sequence[str], None] = "e9a2b3c4d5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notificaciones",
        sa.Column("oculta", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("notificaciones", "oculta")
