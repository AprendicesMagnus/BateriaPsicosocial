"""unir ramas: enlaces para pacientes y perfil / empresas

Une las dos cabezas que dejó el merge 3109cdf:
- a7b8c9d0e1f2 (enlaces para pacientes, rama de cd25a7e)
- c9adf52ace26 (perfil con foto y empresa creadora, rama de 9260592)
No cambia el esquema: cada rama ya agrega sus propias tablas y columnas.

Revision ID: d4c27f0e9b13
Revises: a7b8c9d0e1f2, c9adf52ace26
Create Date: 2026-10-01 12:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'd4c27f0e9b13'
down_revision: Union[str, Sequence[str], None] = ('a7b8c9d0e1f2', 'c9adf52ace26')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
