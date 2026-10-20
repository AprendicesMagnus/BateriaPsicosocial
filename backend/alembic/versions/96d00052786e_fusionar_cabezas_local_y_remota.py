"""fusionar cabezas local y remota

Revision ID: 96d00052786e
Revises: 7a6fb3406e9c, a2e1dfff75a0
Create Date: 2026-10-16 15:02:54.935911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96d00052786e'
down_revision: Union[str, Sequence[str], None] = ('7a6fb3406e9c', 'a2e1dfff75a0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
