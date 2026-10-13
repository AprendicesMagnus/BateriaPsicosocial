"""Fusionar cabezas de migraciones

Revision ID: 34a1a7831787
Revises: d4c27f0e9b13, add_wompi_fields
Create Date: 2026-10-01 21:13:50.654657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34a1a7831787'
down_revision: Union[str, Sequence[str], None] = ('d4c27f0e9b13', 'add_wompi_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
