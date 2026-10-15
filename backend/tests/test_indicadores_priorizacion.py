import uuid
import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Organizacion
from app.models.survey import Dimension, Recomendacion
from app.models.user import Usuario


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_priorizacion_intervenciones_ranking_y_seguimiento(client, db_session, crear_paciente):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Organización
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Priorizacion SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()
    org_id = org.id

    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    # Obtener 3 dimensiones existentes
    dims = db_session.query(Dimension).limit(3).all()
    assert len(dims) >= 3, "Se requieren al menos 3 dimensiones sembradas"
    dim1, dim2, dim3 = dims[0], dims[1], dims[2]

    # Crear una recomendación para dim1 con nivel MUY_ALTO
    rec1 = Recomendacion(
        id=uuid.uuid4(),
        dimension_id=dim1.id,
        nivel="MUY_ALTO",
        titulo="Intervención Prioritaria Dim1",
        descripcion="Acción correctiva inmediata",
        prioridad=1,
    )
    db_session.add(rec1)
    db_session.commit()

    # Evaluación para la organización
    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        organizacion_id=org_id,
        evaluador_id=admin_user.id,
        nombre="Evaluación Priorización 2026",
    )
    db_session.add(evaluacion)
    db_session.commit()

    def _crear_participante_con_resultado(dim_id, nivel):
        p_id, _ = crear_paciente(org_id)
        part = EvaluacionParticipante(
            id=uuid.uuid4(),
            evaluacion_id=evaluacion.id,
            trabajador_id=p_id,
            estado="COMPLETADA",
        )
        db_session.add(part)
        db_session.flush()

        res_dim = ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim_id,
            puntaje_bruto=50.0,
            puntaje_transformado=50.0,
            nivel=nivel,
        )
        db_session.add(res_dim)

    # 1. Dimensión 1: 5 participantes (2 MUY_ALTO, 2 ALTO, 1 MEDIO)
    for n in ["MUY_ALTO", "MUY_ALTO", "ALTO", "ALTO", "MEDIO"]:
        _crear_participante_con_resultado(dim1.id, n)

    # 2. Dimensión 2: 5 participantes con menor riesgo (1 ALTO, 4 BAJO)
    for n in ["ALTO", "BAJO", "BAJO", "BAJO", "BAJO"]:
        _crear_participante_con_resultado(dim2.id, n)

    # 3. Dimensión 3: solo 3 participantes (3 MUY_ALTO) -> debe quedar oculta
    for n in ["MUY_ALTO", "MUY_ALTO", "MUY_ALTO"]:
        _crear_participante_con_resultado(dim3.id, n)

    db_session.commit()

    # Primera consulta GET
    res = client.get(f"/api/indicadores/priorizacion?organizacion_id={org_id}", headers=headers_admin)
    assert res.status_code == 200, res.text
    data = res.json()

    # Dimensión 3 oculta
    assert data["dimensionesOcultas"] == 1
    dims_res = data["dimensiones"]
    assert len(dims_res) == 2

    # Dimensión 1 debe ser la primera en el ranking
    d1_res = dims_res[0]
    assert d1_res["id"] == str(dim1.id)
    assert d1_res["total"] == 5
    assert d1_res["indice"] == 1.2
    assert d1_res["porcentajeAltoMuyAlto"] == 80.0

    # Dimensión 2 aparece después en el ranking
    d2_res = dims_res[1]
    assert d2_res["id"] == str(dim2.id)
    assert d2_res["indice"] == 0.2
    assert d2_res["porcentajeAltoMuyAlto"] == 20.0

    # Recomendación de dim1 aparece con estadoSeguimiento None
    rec_item = next((r for r in d1_res["recomendaciones"] if r["id"] == str(rec1.id)), None)
    assert rec_item is not None
    assert rec_item["nivel"] == "MUY_ALTO"
    assert rec_item["estadoSeguimiento"] is None

    # Registrar la recomendación en el plan de acción con POST /api/seguimiento-recomendaciones
    res_post = client.post(
        "/api/seguimiento-recomendaciones",
        headers=headers_admin,
        json={
            "organizacionId": str(org_id),
            "recomendacionId": str(rec1.id),
            "estado": "PENDIENTE",
        },
    )
    assert res_post.status_code == 200, res_post.text

    # Segunda consulta GET: ahora estadoSeguimiento debe ser "PENDIENTE"
    res_segunda = client.get(f"/api/indicadores/priorizacion?organizacion_id={org_id}", headers=headers_admin)
    assert res_segunda.status_code == 200, res_segunda.text
    data_segunda = res_segunda.json()

    d1_segunda = data_segunda["dimensiones"][0]
    rec_actualizada = next((r for r in d1_segunda["recomendaciones"] if r["id"] == str(rec1.id)), None)
    assert rec_actualizada is not None
    assert rec_actualizada["estadoSeguimiento"] == "PENDIENTE"
