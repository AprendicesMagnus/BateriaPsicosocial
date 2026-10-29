"""aceptacion de la politica de datos en usuarios

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


def _tiene_columna(tabla: str, columna: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return columna in {c["name"] for c in inspector.get_columns(tabla)}


def upgrade() -> None:
    if not _tiene_columna("usuarios", "politica_version"):
        op.add_column("usuarios", sa.Column("politica_version", sa.String(length=20), nullable=True))
    if not _tiene_columna("usuarios", "politica_aceptada_en"):
        op.add_column("usuarios", sa.Column("politica_aceptada_en", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    if _tiene_columna("usuarios", "politica_aceptada_en"):
        op.drop_column("usuarios", "politica_aceptada_en")
    if _tiene_columna("usuarios", "politica_version"):
        op.drop_column("usuarios", "politica_version")
