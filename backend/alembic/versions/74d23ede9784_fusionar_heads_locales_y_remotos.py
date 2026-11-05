"""Fusionar heads locales y remotos.

Revision ID: 74d23ede9784
Revises: d8f3a1c6b2e4, cb19cdbbea43
Create Date: 2026-10-29 15:54:48.404956
"""

from typing import Sequence, Union

from alembic import op


revision: str = "74d23ede9784"
down_revision: Union[str, Sequence[str], None] = (
    "d8f3a1c6b2e4",
    "cb19cdbbea43",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass