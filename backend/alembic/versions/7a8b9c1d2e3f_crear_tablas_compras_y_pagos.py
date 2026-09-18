"""crear_tablas_compras_y_pagos

Revision ID: 7a8b9c1d2e3f
Revises: 1e3f73d3c69d
Create Date: 2026-09-17 20:53:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7a8b9c1d2e3f'
down_revision: Union[str, Sequence[str], None] = '1e3f73d3c69d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'compras',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('usuario_id', sa.UUID(), nullable=False),
        sa.Column('organizacion_id', sa.UUID(), nullable=True),
        sa.Column('bateria_nombre', sa.String(length=150), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('tarifa_unitario', sa.Float(), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('iva', sa.Float(), nullable=False),
        sa.Column('total', sa.Float(), nullable=False),
        sa.Column('estado', sa.String(length=30), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organizacion_id'], ['organizaciones.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'pagos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('compra_id', sa.UUID(), nullable=False),
        sa.Column('metodo', sa.String(length=30), nullable=False),
        sa.Column('referencia', sa.String(length=80), nullable=False),
        sa.Column('monto', sa.Float(), nullable=False),
        sa.Column('estado', sa.String(length=30), nullable=False),
        sa.Column('banco', sa.String(length=80), nullable=True),
        sa.Column('ultimos_digitos', sa.String(length=4), nullable=True),
        sa.Column('titular', sa.String(length=150), nullable=True),
        sa.Column('mensaje_respuesta', sa.String(length=255), nullable=True),
        sa.Column('procesado_en', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['compra_id'], ['compras.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referencia')
    )


def downgrade() -> None:
    op.drop_table('pagos')
    op.drop_table('compras')
