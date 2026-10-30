"""Agregar verificación en dos pasos, sesiones activas y dispositivos confiables.

Revision ID: e8f1c2a4b6d8
Revises: f3a4b5c6d7e8, d8f3a1c6b2e4
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e8f1c2a4b6d8"
down_revision: Union[str, Sequence[str], None] = ("f3a4b5c6d7e8", "d8f3a1c6b2e4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "codigos_2fa",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo_hash", sa.String(length=64), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_codigos_2fa_usuario_id", "codigos_2fa", ["usuario_id"])

    op.create_table(
        "sesiones_activas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_id", sa.String(length=36), nullable=False),
        sa.Column("dispositivo", sa.String(length=255), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expiracion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_id"),
    )
    op.create_index("ix_sesiones_activas_usuario_id", "sesiones_activas", ["usuario_id"])

    op.create_table(
        "dispositivos_confiables",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_dispositivos_confiables_usuario_id", "dispositivos_confiables", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_dispositivos_confiables_usuario_id", table_name="dispositivos_confiables")
    op.drop_table("dispositivos_confiables")
    op.drop_index("ix_sesiones_activas_usuario_id", table_name="sesiones_activas")
    op.drop_table("sesiones_activas")
    op.drop_index("ix_codigos_2fa_usuario_id", table_name="codigos_2fa")
    op.drop_table("codigos_2fa")
