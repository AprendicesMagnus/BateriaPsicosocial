"""verificacion autenticidad informes

Revision ID: d1e2f3a4b5c6
Revises: b7c1d9e4f2a8
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "b7c1d9e4f2a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tiene_columna(tabla: str, columna: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return columna in {c["name"] for c in inspector.get_columns(tabla)}


def _tiene_indice(tabla: str, indice: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return indice in {i["name"] for i in inspector.get_indexes(tabla)}


def upgrade() -> None:
    if not _tiene_columna("informes", "codigo_verificacion"):
        op.add_column("informes", sa.Column("codigo_verificacion", sa.String(40), nullable=True))
    if not _tiene_columna("informes", "hash_sha256"):
        op.add_column("informes", sa.Column("hash_sha256", sa.String(64), nullable=True))
    if not _tiene_indice("informes", "ix_informes_codigo_verificacion"):
        op.create_index("ix_informes_codigo_verificacion", "informes", ["codigo_verificacion"], unique=True)


def downgrade() -> None:
    if _tiene_indice("informes", "ix_informes_codigo_verificacion"):
        op.drop_index("ix_informes_codigo_verificacion", table_name="informes")
    if _tiene_columna("informes", "hash_sha256"):
        op.drop_column("informes", "hash_sha256")
    if _tiene_columna("informes", "codigo_verificacion"):
        op.drop_column("informes", "codigo_verificacion")
