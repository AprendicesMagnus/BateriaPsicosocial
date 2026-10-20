"""unificar_cabezas_actuales

Revision ID: 24c9bb1e431b
Revises: 96d00052786e, e5a1c3f9b7d4
Create Date: 2026-10-19 16:19:22.189329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24c9bb1e431b'
down_revision: Union[str, Sequence[str], None] = 'e5a1c3f9b7d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
