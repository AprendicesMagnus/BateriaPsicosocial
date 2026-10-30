"""Fusionar cabezas de migración

Revision ID: 87a7c3c1661c
Revises: 7fee5d1fd6c1, a9b8c7d6e5f4
Create Date: 2026-10-30 15:27:26.156868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87a7c3c1661c'
down_revision: Union[str, Sequence[str], None] = ('7fee5d1fd6c1', 'a9b8c7d6e5f4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
