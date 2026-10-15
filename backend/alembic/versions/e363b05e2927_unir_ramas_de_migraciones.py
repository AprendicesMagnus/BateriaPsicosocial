"""unir ramas de migraciones

Revision ID: e363b05e2927
Revises: 34a1a7831787, a9c3e5f7b2d1
Create Date: 2026-10-13 15:35:34.981811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e363b05e2927'
down_revision: Union[str, Sequence[str], None] = ('34a1a7831787', 'a9c3e5f7b2d1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
