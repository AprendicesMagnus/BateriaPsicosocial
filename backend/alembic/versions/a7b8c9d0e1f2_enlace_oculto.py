"""enlace oculto

Fecha en que el enlace se quitó de la lista "Enlaces para pacientes" (botón Eliminar o limpieza
automática cada 4 horas). La evaluación y sus respuestas se conservan para "Encuestas realizadas".

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-10-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('evaluaciones', sa.Column('enlace_oculto_en', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('evaluaciones', 'enlace_oculto_en')
