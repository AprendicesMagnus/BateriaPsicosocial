"""crear_tabla_seguimiento_recomendaciones

Revision ID: e5f6a7b8c9d0
Revises: c4f1a2b3d5e6
Create Date: 2026-09-25 17:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "c4f1a2b3d5e6"
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
    if not _hay_tabla('seguimiento_recomendaciones'):
        op.create_table(
            "seguimiento_recomendaciones",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("organizacion_id", sa.UUID(), nullable=False),
            sa.Column("recomendacion_id", sa.UUID(), nullable=False),
            sa.Column("estado", sa.String(length=20), server_default="PENDIENTE", nullable=False),
            sa.Column("responsable", sa.String(length=180), nullable=True),
            sa.Column("fecha_estado", sa.DateTime(timezone=True), nullable=False),
            sa.Column("notas", sa.Text(), nullable=True),
            sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["organizacion_id"], ["organizaciones.id"]),
            sa.ForeignKeyConstraint(["recomendacion_id"], ["recomendaciones.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("organizacion_id", "recomendacion_id", name="uq_seguimiento_org_rec"),
        )


def downgrade() -> None:
    op.drop_table("seguimiento_recomendaciones")
