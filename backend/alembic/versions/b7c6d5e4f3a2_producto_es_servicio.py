"""productos: bandera es_servicio (sin stock)

Revision ID: b7c6d5e4f3a2
Revises: a9b8c7d6e5f4
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c6d5e4f3a2"
down_revision: Union[str, Sequence[str], None] = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("es_servicio", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Los productos de la categoría Tecnología ya se trataban como servicios.
    op.execute(
        "UPDATE productos SET es_servicio = TRUE "
        "WHERE lower(translate(trim(categoria), 'íÍ', 'iI')) = 'tecnologia'"
    )


def downgrade() -> None:
    op.drop_column("productos", "es_servicio")
