"""crear_tabla_recomendaciones

Revision ID: 1e3f73d3c69d
Revises: 60de8afddc4a
Create Date: 2026-09-16 14:31:28.995551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e3f73d3c69d'
down_revision: Union[str, Sequence[str], None] = '60de8afddc4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'recomendaciones',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dimension_id', sa.UUID(), nullable=False),
        sa.Column('nivel', sa.String(length=30), nullable=False),
        sa.Column('titulo', sa.String(length=180), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('prioridad', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['dimension_id'], ['dimensiones.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('recomendaciones')
