import uuid
import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Area, Organizacion
from app.models.survey import CuestionarioVersion, Dimension
from app.models.user import Usuario


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_indicadores_filtro_por_area(client, db_session, crear_paciente):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Organización y Áreas
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Filtro Area SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()
    org_id = org.id

    area_a = Area(id=uuid.uuid4(), organizacion_id=org_id, nombre="Área A")
    area_b = Area(id=uuid.uuid4(), organizacion_id=org_id, nombre="Área B")
    db_session.add_all([area_a, area_b])
    db_session.commit()

    dim = db_session.query(Dimension).first()
    assert dim is not None
    cuestionario = db_session.query(CuestionarioVersion).filter(CuestionarioVersion.id == dim.version_id).first()
    assert cuestionario is not None

    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        organizacion_id=org_id,
        evaluador_id=admin_user.id,
        nombre="Evaluación Filtro Área 2026",
    )
    db_session.add(evaluacion)
    db_session.commit()

    def _crear_participante(area_id, nivel="MEDIO"):
        paciente_id, _ = crear_paciente(org_id, area_id=area_id)
        part = EvaluacionParticipante(
            id=uuid.uuid4(),
            evaluacion_id=evaluacion.id,
            trabajador_id=paciente_id,
            estado="COMPLETADA",
        )
        db_session.add(part)
        db_session.flush()

        res_dim = ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=50.0,
            puntaje_transformado=50.0,
            nivel=nivel,
        )
        db_session.add(res_dim)
        return part

    # Área A con 6 pacientes completados
    for _ in range(6):
        _crear_participante(area_a.id, "MEDIO")

    # Área B con 2 pacientes completados
    for _ in range(2):
        _crear_participante(area_b.id, "ALTO")

    db_session.commit()

    # Caso (a): GET /api/indicadores?area_id=A devuelve participacion.totalCompletados == 6 y distribucionRiesgo con datos
    res_a = client.get(
        f"/api/indicadores?organizacion_id={org_id}&area_id={area_a.id}",
        headers=headers_admin,
    )
    assert res_a.status_code == 200, res_a.text
    data_a = res_a.json()
    assert data_a["participacion"]["totalCompletados"] == 6
    assert data_a["anonimizado"] is False
    assert data_a["distribucionRiesgo"] is not None
    assert data_a["distribucionRiesgo"]["MEDIO"] == 6

    # Caso (b): con area_id=B devuelve anonimizado True y distribucionRiesgo None
    res_b = client.get(
        f"/api/indicadores?organizacion_id={org_id}&area_id={area_b.id}",
        headers=headers_admin,
    )
    assert res_b.status_code == 200, res_b.text
    data_b = res_b.json()
    assert data_b["participacion"]["totalCompletados"] == 2
    assert data_b["anonimizado"] is True
    assert data_b["distribucionRiesgo"] is None

    # Caso (c): /api/indicadores/por-categoria?area_id=B devuelve anonimizado True
    res_cat_b = client.get(
        f"/api/indicadores/por-categoria?organizacion_id={org_id}&area_id={area_b.id}",
        headers=headers_admin,
    )
    assert res_cat_b.status_code == 200, res_cat_b.text
    data_cat_b = res_cat_b.json()
    assert cuestionario.codigo in data_cat_b["categorias"]
    assert data_cat_b["categorias"][cuestionario.codigo]["anonimizado"] is True
    assert data_cat_b["categorias"][cuestionario.codigo]["distribucion"] is None

    # Caso (d): sin area_id las cifras son iguales a las de antes del filtro (total de ambas áreas)
    res_total = client.get(
        f"/api/indicadores?organizacion_id={org_id}",
        headers=headers_admin,
    )
    assert res_total.status_code == 200, res_total.text
    data_total = res_total.json()
    assert data_total["participacion"]["totalCompletados"] == 8
    assert data_total["anonimizado"] is False
    assert data_total["distribucionRiesgo"] is not None
    assert data_total["distribucionRiesgo"]["MEDIO"] == 6
    assert data_total["distribucionRiesgo"]["ALTO"] == 2

    res_cat_total = client.get(
        f"/api/indicadores/por-categoria?organizacion_id={org_id}",
        headers=headers_admin,
    )
    assert res_cat_total.status_code == 200, res_cat_total.text
    data_cat_total = res_cat_total.json()
    assert cuestionario.codigo in data_cat_total["categorias"]
    assert data_cat_total["categorias"][cuestionario.codigo]["anonimizado"] is False
    assert data_cat_total["categorias"][cuestionario.codigo]["distribucion"] is not None
