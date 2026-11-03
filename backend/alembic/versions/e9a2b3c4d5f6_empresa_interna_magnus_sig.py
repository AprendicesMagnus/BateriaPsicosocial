"""Registrar MAGNUS | SIG como empresa interna y asociarla a superadministradores."""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "e9a2b3c4d5f6"
down_revision: Union[str, Sequence[str], None] = "648bfbcd632c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOMBRE = "MAGNUS | SIG"
NIT = "1075277687-2"


def upgrade() -> None:
    bind = op.get_bind()
    fila = bind.execute(
        sa.text("SELECT id FROM organizaciones WHERE nit = :nit LIMIT 1"),
        {"nit": NIT},
    ).first()

    if fila is None:
        # Evita crear una segunda fila si la empresa ya existía con el mismo nombre.
        fila = bind.execute(
            sa.text("SELECT id FROM organizaciones WHERE lower(trim(nombre)) = lower(:nombre) LIMIT 1"),
            {"nombre": NOMBRE},
        ).first()

    if fila is None:
        organizacion_id = uuid.uuid4()
        bind.execute(
            sa.text(
                """INSERT INTO organizaciones (id, nombre, nit, activa, creado_en)
                   VALUES (:id, :nombre, :nit, TRUE, now())"""
            ),
            {"id": organizacion_id, "nombre": NOMBRE, "nit": NIT},
        )
    else:
        organizacion_id = fila.id
        bind.execute(
            sa.text(
                """UPDATE organizaciones
                   SET nombre = :nombre, nit = :nit, activa = TRUE
                   WHERE id = :id"""
            ),
            {"id": organizacion_id, "nombre": NOMBRE, "nit": NIT},
        )

    bind.execute(
        sa.text(
            """UPDATE usuarios AS u
               SET organizacion_id = :organizacion_id
               FROM roles AS r
               WHERE u.rol_id = r.id
                 AND r.codigo = 'SUPER_ADMINISTRADOR'
                 AND u.organizacion_id IS DISTINCT FROM :organizacion_id"""
        ),
        {"organizacion_id": organizacion_id},
    )


def downgrade() -> None:
    # No se elimina la organización en downgrade para evitar borrar datos que
    # pudieran haberse asociado después. Solo se desasocia de superadministradores.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """UPDATE usuarios
               SET organizacion_id = NULL
               WHERE organizacion_id = (
                   SELECT id FROM organizaciones WHERE nit = :nit LIMIT 1
               )
               AND rol_id IN (SELECT id FROM roles WHERE codigo = 'SUPER_ADMINISTRADOR')"""
        ),
        {"nit": NIT},
    )
