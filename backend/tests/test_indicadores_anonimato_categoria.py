import uuid
import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Organizacion
from app.models.survey import CuestionarioVersion, Dimension
from app.models.user import Usuario


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_anonimato_por_categoria_cuenta_personas(client, db_session, crear_paciente):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Organización
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Anonimato Test SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()
    org_id = org.id

    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    # Crear Evaluación
    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        organizacion_id=org_id,
        evaluador_id=admin_user.id,
        nombre="Evaluación Anonimato 2026",
    )
    db_session.add(evaluacion)
    db_session.commit()

    # Buscar un cuestionario que tenga al menos 5 dimensiones
    cuestionarios = db_session.query(CuestionarioVersion).all()
    cuestionario_target = None
    dimensiones_target = []
    for c in cuestionarios:
        dims = db_session.query(Dimension).filter(Dimension.version_id == c.id).all()
        if len(dims) >= 5:
            cuestionario_target = c
            dimensiones_target = dims[:5]
            break

    assert cuestionario_target is not None, "Debe existir un cuestionario con al menos 5 dimensiones"
    codigo_target = cuestionario_target.codigo

    # Caso (a): un solo paciente con evaluación COMPLETADA y resultados de varias dimensiones (5 dimensiones)
    paciente_1_id, _ = crear_paciente(org_id)
    part_1 = EvaluacionParticipante(
        id=uuid.uuid4(),
        evaluacion_id=evaluacion.id,
        trabajador_id=paciente_1_id,
        estado="COMPLETADA",
    )
    db_session.add(part_1)
    db_session.flush()

    for dim in dimensiones_target:
        res_dim = ResultadoDimension(
            participante_id=part_1.id,
            dimension_id=dim.id,
            puntaje_bruto=50.0,
            puntaje_transformado=50.0,
            nivel="MEDIO",
        )
        db_session.add(res_dim)
    db_session.commit()

    # Consultar endpoint: debe devolver anonimizado=True y distribucion=None para esa categoría
    res_a = client.get(
        f"/api/indicadores/por-categoria?organizacion_id={org_id}",
        headers=headers_admin,
    )
    assert res_a.status_code == 200, res_a.text
    data_a = res_a.json()
    assert codigo_target in data_a["categorias"]
    cat_a = data_a["categorias"][codigo_target]
    assert cat_a["anonimizado"] is True
    assert cat_a["distribucion"] is None
    assert cat_a["mensajeAnonimato"] is not None

    # Caso (b): cinco pacientes completados (agregar 4 más)
    for _ in range(4):
        paciente_id, _ = crear_paciente(org_id)
        part = EvaluacionParticipante(
            id=uuid.uuid4(),
            evaluacion_id=evaluacion.id,
            trabajador_id=paciente_id,
            estado="COMPLETADA",
        )
        db_session.add(part)
        db_session.flush()

        for dim in dimensiones_target:
            res_dim = ResultadoDimension(
                participante_id=part.id,
                dimension_id=dim.id,
                puntaje_bruto=50.0,
                puntaje_transformado=50.0,
                nivel="MEDIO",
            )
            db_session.add(res_dim)
    db_session.commit()

    # Consultar endpoint: debe devolver anonimizado=False y distribucion con datos
    res_b = client.get(
        f"/api/indicadores/por-categoria?organizacion_id={org_id}",
        headers=headers_admin,
    )
    assert res_b.status_code == 200, res_b.text
    data_b = res_b.json()
    assert codigo_target in data_b["categorias"]
    cat_b = data_b["categorias"][codigo_target]
    assert cat_b["anonimizado"] is False
    assert cat_b["distribucion"] is not None
    assert cat_b["distribucion"]["MEDIO"] > 0
    assert cat_b["mensajeAnonimato"] is None
