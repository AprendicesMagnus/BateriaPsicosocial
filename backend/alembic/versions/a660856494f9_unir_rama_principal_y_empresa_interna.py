"""unir rama principal y empresa interna

Revision ID: a660856494f9
Revises: 74d23ede9784, e9a2b3c4d5f6
Create Date: 2026-11-04 15:07:13.301346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a660856494f9'
down_revision: Union[str, Sequence[str], None] = ('74d23ede9784', 'e9a2b3c4d5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
