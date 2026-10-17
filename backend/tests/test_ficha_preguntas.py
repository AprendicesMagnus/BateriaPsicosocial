import pytest

from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Respuesta
from app.models.survey import CuestionarioVersion, Dimension, Pregunta


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_ficha_tiene_21_preguntas(db_session):
    v_ficha = (
        db_session.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == "FICHA_DATOS", CuestionarioVersion.vigente.is_(True))
        .first()
    )
    assert v_ficha is not None, "No se encontró la versión vigente de FICHA_DATOS."

    dimension = (
        db_session.query(Dimension)
        .filter(Dimension.version_id == v_ficha.id, Dimension.codigo == "DATOS_SOCIO_LABORALES")
        .first()
    )
    assert dimension is not None, "No se encontró la dimensión DATOS_SOCIO_LABORALES de la ficha."

    preguntas = db_session.query(Pregunta).filter(Pregunta.dimension_id == dimension.id).all()
    codigos = {p.codigo for p in preguntas}

    esperados = {f"F{i}" for i in range(1, 22)}
    assert codigos == esperados, f"Se esperaban códigos {esperados}, pero se encontraron {codigos}"
    assert len(preguntas) == 21, f"Se esperaban 21 preguntas, se encontraron {len(preguntas)}"

    pregunta_f20 = next(p for p in preguntas if p.codigo == "F20")
    pregunta_f21 = next(p for p in preguntas if p.codigo == "F21")

    assert pregunta_f20.tipo_respuesta == "ENTERO"
    assert pregunta_f21.tipo_respuesta == "SELECCION"


def test_seed_restaura_preguntas_faltantes(db_session):
    v_ficha = (
        db_session.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == "FICHA_DATOS", CuestionarioVersion.vigente.is_(True))
        .first()
    )
    assert v_ficha is not None

    dimension = (
        db_session.query(Dimension)
        .filter(Dimension.version_id == v_ficha.id, Dimension.codigo == "DATOS_SOCIO_LABORALES")
        .first()
    )
    assert dimension is not None

    try:
        preguntas_eliminar = (
            db_session.query(Pregunta)
            .filter(Pregunta.dimension_id == dimension.id, Pregunta.codigo.in_(["F20", "F21"]))
            .all()
        )
        ids_eliminar = [p.id for p in preguntas_eliminar]

        # Borrar respuestas asociadas si existieran
        db_session.query(Respuesta).filter(Respuesta.pregunta_id.in_(ids_eliminar)).delete(
            synchronize_session=False
        )

        # Borrar las preguntas F20 y F21
        db_session.query(Pregunta).filter(Pregunta.id.in_(ids_eliminar)).delete(
            synchronize_session=False
        )
        db_session.flush()

        # Verificar que ya no existen
        codigos_actuales = {
            codigo
            for (codigo,) in db_session.query(Pregunta.codigo)
            .filter(Pregunta.dimension_id == dimension.id)
            .all()
        }
        assert "F20" not in codigos_actuales
        assert "F21" not in codigos_actuales

        # Volver a llamar sembrar_todos_los_cuestionarios
        sembrar_todos_los_cuestionarios(db_session)
        db_session.flush()

        # Verificar que F20 y F21 existen de nuevo en la dimensión
        preguntas_restauradas = (
            db_session.query(Pregunta)
            .filter(Pregunta.dimension_id == dimension.id, Pregunta.codigo.in_(["F20", "F21"]))
            .all()
        )
        codigos_restaurados = {p.codigo for p in preguntas_restauradas}
        assert codigos_restaurados == {"F20", "F21"}

    finally:
        db_session.rollback()
