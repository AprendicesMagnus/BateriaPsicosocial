"""agregar respuesta y fecha de respuesta a tickets_soporte

Revision ID: a3c5e7b9d1f2
Revises: d7a1c3e5f9b2
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3c5e7b9d1f2"
down_revision: Union[str, Sequence[str], None] = "d7a1c3e5f9b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tickets_soporte", sa.Column("respuesta", sa.Text(), nullable=True))
    op.add_column("tickets_soporte", sa.Column("respondido_en", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets_soporte", "respondido_en")
    op.drop_column("tickets_soporte", "respuesta")
