"""instrumentos ficha y filtros

Revision ID: 34da4d0b8f22
Revises: 7a8b9c1d2e3f
Create Date: 2026-09-28 11:48:59.092438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34da4d0b8f22'
down_revision: Union[str, Sequence[str], None] = '7a8b9c1d2e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Instanciamos el inspector para comprobar qué elementos ya existen en la Base de Datos
    inspector = sa.inspect(op.get_bind())
    tablas_existentes = inspector.get_table_names()

    # 1. Crear tabla seguimiento_recomendaciones si no existe
    if 'seguimiento_recomendaciones' not in tablas_existentes:
        op.create_table('seguimiento_recomendaciones',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organizacion_id', sa.UUID(), nullable=False),
        sa.Column('recomendacion_id', sa.UUID(), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('responsable', sa.String(length=180), nullable=True),
        sa.Column('fecha_estado', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organizacion_id'], ['organizaciones.id'], ),
        sa.ForeignKeyConstraint(['recomendacion_id'], ['recomendaciones.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organizacion_id', 'recomendacion_id', name='uq_seguimiento_org_rec')
        )

    # 2. Crear tabla evaluacion_instrumentos si no existe
    if 'evaluacion_instrumentos' not in tablas_existentes:
        op.create_table('evaluacion_instrumentos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('evaluacion_id', sa.UUID(), nullable=False),
        sa.Column('version_id', sa.UUID(), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.Column('obligatorio', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['evaluacion_id'], ['evaluaciones.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['cuestionario_versiones.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evaluacion_id', 'version_id', name='uq_eval_version_instrumento')
        )

    # 3. Crear tabla participante_instrumentos si no existe
    if 'participante_instrumentos' not in tablas_existentes:
        op.create_table('participante_instrumentos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('participante_id', sa.UUID(), nullable=False),
        sa.Column('instrumento_id', sa.UUID(), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('fecha_inicio', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_fin', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['instrumento_id'], ['evaluacion_instrumentos.id'], ),
        sa.ForeignKeyConstraint(['participante_id'], ['evaluacion_participantes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('participante_id', 'instrumento_id', name='uq_participante_instrumento')
        )

    # Inspeccionar columnas para las tablas que se van a alterar
    columnas_dimensiones = [c['name'] for c in inspector.get_columns('dimensiones')]
    columnas_preguntas = [c['name'] for c in inspector.get_columns('preguntas')]

    # 4. Agregar columnas a dimensiones de forma segura
    if 'tipo' not in columnas_dimensiones:
        op.add_column('dimensiones', sa.Column('tipo', sa.String(length=20), nullable=False, server_default='DIMENSION'))
    
    if 'factor_transformacion' not in columnas_dimensiones:
        op.add_column('dimensiones', sa.Column('factor_transformacion', sa.Float(), nullable=True))

    # 5. Modificar la columna version_id en evaluaciones
    op.alter_column('evaluaciones', 'version_id',
               existing_type=sa.UUID(),
               nullable=True)

    # 6. Agregar columnas a preguntas de forma segura
    if 'tipo_respuesta' not in columnas_preguntas:
        op.add_column('preguntas', sa.Column('tipo_respuesta', sa.String(length=20), nullable=False, server_default='LIKERT'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('preguntas', 'tipo_respuesta')
    op.alter_column('evaluaciones', 'version_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.drop_column('dimensiones', 'factor_transformacion')
    op.drop_column('dimensiones', 'tipo')
    op.drop_table('participante_instrumentos')
    op.drop_table('evaluacion_instrumentos')
    op.drop_table('seguimiento_recomendaciones')
