"""Fusionar cabezas de migracion

Revision ID: 76ec0d8feeb1
Revises: 87a7c3c1661c, b7c6d5e4f3a2
Create Date: 2026-10-30 15:51:03.138938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76ec0d8feeb1'
down_revision: Union[str, Sequence[str], None] = ('87a7c3c1661c', 'b7c6d5e4f3a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
