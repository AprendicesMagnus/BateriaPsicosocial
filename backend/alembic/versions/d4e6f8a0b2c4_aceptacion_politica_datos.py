
"""Aceptacion de politica de datos.

Revision ID: d4e6f8a0b2c4
Revises: cb19cdbbea43
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e6f8a0b2c4"
down_revision: Union[str, Sequence[str], None] = "cb19cdbbea43"

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columnas = {
        columna["name"]
        for columna in inspector.get_columns("usuarios")
    }

    if "politica_version" not in columnas:
        op.add_column(
            "usuarios",
            sa.Column("politica_version", sa.String(length=20), nullable=True),
        )

    if "politica_aceptada_en" not in columnas:
        op.add_column(
            "usuarios",
            sa.Column(
                "politica_aceptada_en",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )


def downgrade() -> None:
    # Se conservan estas columnas para evitar eliminar datos
    # que podrían existir antes de ejecutar esta migración.
    pass
