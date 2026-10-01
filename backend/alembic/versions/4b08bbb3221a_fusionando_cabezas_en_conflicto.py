"""Fusionando cabezas en conflicto

Revision ID: 4b08bbb3221a
Revises: 5cd71dd1f202, f1a2b3c4d5e6
Create Date: 2026-09-30 17:07:05.279759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b08bbb3221a'
down_revision: Union[str, Sequence[str], None] = ('5cd71dd1f202', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
