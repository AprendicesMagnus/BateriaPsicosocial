"""Controlar la disponibilidad y el consumo de baterías por primera respuesta.

Revision ID: ef31a7c9b205
Revises: d88cd16e5cba
Create Date: 2026-11-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "ef31a7c9b205"
down_revision: Union[str, Sequence[str], None] = "d88cd16e5cba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guardar el plan seleccionado como referencia y como nombre histórico para el seguimiento.
    op.add_column("compras", sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("compras", sa.Column("plan_nombre", sa.String(length=150), nullable=True))
    op.create_foreign_key(
        "fk_compras_plan_id_planes_baterias",
        "compras",
        "planes_baterias",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "evaluaciones",
        sa.Column("bateria_controlada", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "evaluaciones",
        sa.Column("bateria_consumida_en", sa.DateTime(timezone=True), nullable=True),
    )
    # Los enlaces históricos de usuarios normales también quedan bajo el control.
    # Solo se marcan consumidos los que
    # realmente guardaron la Ficha o alguna respuesta; abrir el enlace no consume.
    op.execute("""
        UPDATE evaluaciones e
        SET bateria_controlada = TRUE
        FROM usuarios u
        JOIN roles r ON r.id = u.rol_id
        WHERE e.evaluador_id = u.id
          AND r.codigo <> 'SUPER_ADMINISTRADOR'
          AND e.enlace_token IS NOT NULL
    """)
    op.execute("""
        UPDATE evaluaciones e
        SET bateria_consumida_en = COALESCE(
            (SELECT MIN(p.fecha_inicio) FROM evaluacion_participantes p WHERE p.evaluacion_id = e.id AND p.fecha_inicio IS NOT NULL),
            (SELECT MIN(r.actualizado_en) FROM evaluacion_participantes p JOIN respuestas r ON r.participante_id = p.id WHERE p.evaluacion_id = e.id)
        )
        WHERE e.bateria_controlada = TRUE
          AND EXISTS (
              SELECT 1 FROM evaluacion_participantes p
              WHERE p.evaluacion_id = e.id
                AND (p.fecha_inicio IS NOT NULL OR EXISTS (SELECT 1 FROM respuestas r WHERE r.participante_id = p.id))
          )
    """)
    op.alter_column("evaluaciones", "bateria_controlada", server_default=None)


def downgrade() -> None:
    op.drop_column("evaluaciones", "bateria_consumida_en")
    op.drop_column("evaluaciones", "bateria_controlada")
    op.drop_constraint("fk_compras_plan_id_planes_baterias", "compras", type_="foreignkey")
    op.drop_column("compras", "plan_nombre")
    op.drop_column("compras", "plan_id")
