"""add Wompi fields to pagos

Revision ID: add_wompi_fields
Revises: e5f6a7b8c9d0
Create Date: 2026-10-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_wompi_fields"

down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pagos",
        sa.Column(
            "wompi_transaction_id",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "pagos",
        sa.Column(
            "wompi_status",
            sa.String(length=30),
            nullable=True,
        ),
    )

    op.add_column(
        "pagos",
        sa.Column(
            "wompi_payment_method",
            sa.String(length=80),
            nullable=True,
        ),
    )

    op.create_unique_constraint(
        "uq_pagos_wompi_transaction_id",
        "pagos",
        ["wompi_transaction_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_pagos_wompi_transaction_id",
        "pagos",
        type_="unique",
    )

    op.drop_column(
        "pagos",
        "wompi_payment_method",
    )

    op.drop_column(
        "pagos",
        "wompi_status",
    )

    op.drop_column(
        "pagos",
        "wompi_transaction_id",
    )