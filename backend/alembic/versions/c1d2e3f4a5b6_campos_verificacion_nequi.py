"""Agregar datos de verificación manual Nequi sin alterar pagos históricos."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c1d2e3f4a5b6"
down_revision = "b9d3f1a7c2e4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pedidos_productos", sa.Column("organizacion_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_pedidos_productos_organizacion", "pedidos_productos", "organizaciones", ["organizacion_id"], ["id"], ondelete="SET NULL")
    for table in ("pagos", "pagos_pedidos_productos"):
        op.add_column(table, sa.Column("comprobante_path", sa.String(length=255), nullable=True))
        op.add_column(table, sa.Column("observaciones", sa.String(length=500), nullable=True))
        op.add_column(table, sa.Column("revisado_por_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.add_column(table, sa.Column("revisado_en", sa.DateTime(timezone=True), nullable=True))
        op.create_foreign_key(f"fk_{table}_revisado_por", table, "usuarios", ["revisado_por_id"], ["id"], ondelete="SET NULL")


def downgrade():
    for table in ("pagos_pedidos_productos", "pagos"):
        op.drop_constraint(f"fk_{table}_revisado_por", table, type_="foreignkey")
        op.drop_column(table, "revisado_en")
        op.drop_column(table, "revisado_por_id")
        op.drop_column(table, "observaciones")
        op.drop_column(table, "comprobante_path")
    op.drop_constraint("fk_pedidos_productos_organizacion", "pedidos_productos", type_="foreignkey")
    op.drop_column("pedidos_productos", "organizacion_id")
