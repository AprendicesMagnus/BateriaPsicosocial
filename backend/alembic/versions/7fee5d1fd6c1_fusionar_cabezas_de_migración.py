"""Fusionar cabezas de migración

Revision ID: 7fee5d1fd6c1
Revises: d8f3a1c6b2e4, f3a4b5c6d7e8
Create Date: 2026-10-30 14:55:45.927869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fee5d1fd6c1'
down_revision: Union[str, Sequence[str], None] = ('d8f3a1c6b2e4', 'f3a4b5c6d7e8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
