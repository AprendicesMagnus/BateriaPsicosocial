"""agregar fecha_limite a seguimiento_recomendaciones

Revision ID: b7c1d9e4f2a8
Revises: e363b05e2927
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7c1d9e4f2a8"
down_revision: Union[str, Sequence[str], None] = "e363b05e2927"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tiene_columna(tabla: str, columna: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return columna in {c["name"] for c in inspector.get_columns(tabla)}


def upgrade() -> None:
    if not _tiene_columna("seguimiento_recomendaciones", "fecha_limite"):
        op.add_column(
            "seguimiento_recomendaciones",
            sa.Column("fecha_limite", sa.Date(), nullable=True),
        )


def downgrade() -> None:
    if _tiene_columna("seguimiento_recomendaciones", "fecha_limite"):
        op.drop_column("seguimiento_recomendaciones", "fecha_limite")
