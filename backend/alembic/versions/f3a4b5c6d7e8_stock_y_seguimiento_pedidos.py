"""Agregar stock a productos y control de reintegro de inventario en pedidos."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "cb19cdbbea43"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("productos", sa.Column("stock", sa.Integer(), nullable=True))
    # Los productos existentes se inicializan sin inventario confirmado; el administrador debe registrarlo.
    op.execute("UPDATE productos SET stock = 0 WHERE stock IS NULL")
    op.alter_column("productos", "stock", nullable=False, server_default="0")
    op.add_column(
        "pedidos_productos",
        sa.Column("stock_reintegrado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Los pedidos anteriores no reservaron inventario; no deben devolver unidades al cancelarse.
    op.execute("UPDATE pedidos_productos SET stock_reintegrado = TRUE")


def downgrade() -> None:
    op.drop_column("pedidos_productos", "stock_reintegrado")
    op.drop_column("productos", "stock")
