"""Merge de ramas de migraciones

Revision ID: 648bfbcd632c
Revises: 26b983a33314, d4e6f8a0b2c4
Create Date: 2026-10-30 21:17:08.678665

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '648bfbcd632c'
down_revision: Union[str, Sequence[str], None] = ('26b983a33314', 'd4e6f8a0b2c4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
