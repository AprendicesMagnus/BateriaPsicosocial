"""unir ramas

Revision ID: a2e1dfff75a0
Revises: c4e8a2d6f0b1, f2a3b4c5d6e7
Create Date: 2026-10-15 17:18:19.329734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2e1dfff75a0'
down_revision: Union[str, Sequence[str], None] = ('c4e8a2d6f0b1', 'f2a3b4c5d6e7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
