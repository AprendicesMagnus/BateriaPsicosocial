"""fusionar multiples heads

Revision ID: 7f17a0c1ef12
Revises: 76ec0d8feeb1, e8f1c2a4b6d8
Create Date: 2026-10-30 17:38:38.039819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f17a0c1ef12'
down_revision: Union[str, Sequence[str], None] = ('76ec0d8feeb1', 'e8f1c2a4b6d8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
