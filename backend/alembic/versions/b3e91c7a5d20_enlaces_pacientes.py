"""enlaces para pacientes

Agrega el token del enlace público de una evaluación (lo crea el psicólogo / evaluador SST)
y la marca de usuario invitado (paciente que responde por el enlace, sin cuenta propia).

Revision ID: b3e91c7a5d20
Revises: 5cd71dd1f202
Create Date: 2026-09-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3e91c7a5d20'
down_revision: Union[str, Sequence[str], None] = '5cd71dd1f202'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('evaluaciones', sa.Column('enlace_token', sa.String(length=64), nullable=True))
    op.create_unique_constraint('uq_evaluacion_enlace_token', 'evaluaciones', ['enlace_token'])
    op.add_column(
        'usuarios',
        sa.Column('es_invitado', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('usuarios', 'es_invitado')
    op.drop_constraint('uq_evaluacion_enlace_token', 'evaluaciones', type_='unique')
    op.drop_column('evaluaciones', 'enlace_token')
