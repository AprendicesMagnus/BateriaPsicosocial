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


# La rama de 34da4d0b8f22 ya crea estas mismas tablas y columnas; si ya existen se omiten
# para que las dos ramas de migraciones se puedan aplicar sobre la misma base.
def _hay_tabla(tabla: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(tabla)


def _hay_columna(tabla: str, columna: str) -> bool:
    return columna in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(tabla)}


def _hay_fk(tabla: str, nombre: str) -> bool:
    return nombre in {fk["name"] for fk in sa.inspect(op.get_bind()).get_foreign_keys(tabla)}


def upgrade() -> None:
    if not _hay_columna('dimensiones', 'tipo'):
        op.add_column(
            "dimensiones",
            sa.Column("tipo", sa.String(length=20), server_default="DIMENSION", nullable=False),
        )
    if not _hay_columna('dimensiones', 'factor_transformacion'):
        op.add_column(
            "dimensiones",
            sa.Column("factor_transformacion", sa.Float(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("dimensiones", "factor_transformacion")
    op.drop_column("dimensiones", "tipo")
