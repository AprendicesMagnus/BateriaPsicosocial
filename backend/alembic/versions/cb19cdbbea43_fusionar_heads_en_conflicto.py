"""Fusionar heads en conflicto

Revision ID: cb19cdbbea43
Revises: a3c5e7b9d1f2, c6d7e8f9a0b1
Create Date: 2026-10-26 17:33:31.050314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb19cdbbea43'
down_revision: Union[str, Sequence[str], None] = ('a3c5e7b9d1f2', 'c6d7e8f9a0b1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
