"""enlace instrumento unico

Permite crear un enlace restringido a un solo cuestionario (Ficha, Estrés, Extralaboral o
Intralaboral A/B) en vez de la batería completa. "enlace_instrumento" guarda el código del
instrumento al que queda restringido el paciente invitado; "enlace_ruta" guarda la ruta del
frontend (Forma A o B) a la que se le redirige al empezar.

Revision ID: d8f3a1c6b2e4
Revises: 61f92783b1c0
Create Date: 2026-10-27 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f3a1c6b2e4'
down_revision: Union[str, Sequence[str], None] = '61f92783b1c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('evaluaciones', sa.Column('enlace_instrumento', sa.String(length=20), nullable=True))
    op.add_column('evaluaciones', sa.Column('enlace_ruta', sa.String(length=60), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('evaluaciones', 'enlace_ruta')
    op.drop_column('evaluaciones', 'enlace_instrumento')
