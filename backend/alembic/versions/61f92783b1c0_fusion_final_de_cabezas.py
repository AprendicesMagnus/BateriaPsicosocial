"""fusion final de cabezas

Revision ID: 61f92783b1c0
Revises: b11029071c17, f7b2e4a6c8d0
Create Date: 2026-10-20 15:19:19.399615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61f92783b1c0'
down_revision: Union[str, Sequence[str], None] = ('b11029071c17', 'f7b2e4a6c8d0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
