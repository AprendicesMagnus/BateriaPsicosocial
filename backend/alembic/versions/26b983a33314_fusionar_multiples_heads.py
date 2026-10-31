"""Fusionar multiples heads

Revision ID: 26b983a33314
Revises: 3afd748e99c8, 7f17a0c1ef12
Create Date: 2026-10-30 19:03:33.196683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26b983a33314'
down_revision: Union[str, Sequence[str], None] = ('3afd748e99c8', '7f17a0c1ef12')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
