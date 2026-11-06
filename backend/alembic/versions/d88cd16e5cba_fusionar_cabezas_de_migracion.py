"""Fusionar cabezas de migracion

Revision ID: d88cd16e5cba
Revises: a660856494f9, c3e5a7b9d1f2
Create Date: 2026-11-05 18:50:12.888254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd88cd16e5cba'
down_revision: Union[str, Sequence[str], None] = ('a660856494f9', 'c3e5a7b9d1f2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
