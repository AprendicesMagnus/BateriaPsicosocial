"""
Los codigos de pregunta deben ser unicos en toda la base sembrada.

guardar_respuesta busca la Pregunta solo por codigo: si dos instrumentos
compartieran un codigo, la respuesta podria guardarse en la pregunta equivocada.
"""
import pytest
from sqlalchemy import func

from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.survey import Pregunta


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_codigos_de_pregunta_son_unicos(db_session):
    repetidos = (
        db_session.query(Pregunta.codigo, func.count(Pregunta.id))
        .group_by(Pregunta.codigo)
        .having(func.count(Pregunta.id) > 1)
        .all()
    )
    assert not repetidos, f"Codigos de pregunta repetidos: {repetidos[:20]}"