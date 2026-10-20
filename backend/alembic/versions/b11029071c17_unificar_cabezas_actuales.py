"""unificar_cabezas_actuales

Revision ID: b11029071c17
Revises: 24c9bb1e431b, c0c62aed1990
Create Date: 2026-10-19 16:24:06.309313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b11029071c17'
down_revision: Union[str, Sequence[str], None] = '24c9bb1e431b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
