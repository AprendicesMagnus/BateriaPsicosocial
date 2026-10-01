"""perfil: foto y fecha de edición; empresas: usuario creador

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
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
    if not _hay_columna('usuarios', 'foto_url'):
        op.add_column("usuarios", sa.Column("foto_url", sa.String(length=255), nullable=True))
    if not _hay_columna('usuarios', 'perfil_actualizado_en'):
        op.add_column(
            "usuarios",
            sa.Column("perfil_actualizado_en", sa.DateTime(timezone=True), nullable=True),
        )
    if not _hay_columna('organizaciones', 'creada_por_id'):
        op.add_column(
            "organizaciones",
            sa.Column("creada_por_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not _hay_fk('organizaciones', 'fk_organizaciones_creada_por'):
        op.create_foreign_key(
            "fk_organizaciones_creada_por", "organizaciones", "usuarios", ["creada_por_id"], ["id"]
        )


def downgrade() -> None:
    op.drop_constraint("fk_organizaciones_creada_por", "organizaciones", type_="foreignkey")
    op.drop_column("organizaciones", "creada_por_id")
    op.drop_column("usuarios", "perfil_actualizado_en")
    op.drop_column("usuarios", "foto_url")
