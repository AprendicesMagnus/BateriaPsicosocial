"""Fusionar cabezas de migración

Revision ID: c0c62aed1990
Revises: 7a6fb3406e9c, d2f4b6a8c0e2
Create Date: 2026-10-16 16:27:05.330784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0c62aed1990'
down_revision: Union[str, Sequence[str], None] = ('7a6fb3406e9c', 'd2f4b6a8c0e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
