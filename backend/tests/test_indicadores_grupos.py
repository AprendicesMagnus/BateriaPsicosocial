import uuid
import pytest

from app.core.encryption import cifrar_json
from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Respuesta, ResultadoDimension
from app.models.organization import Organizacion
from app.models.survey import CuestionarioVersion, Dimension, Pregunta
from app.models.user import Usuario


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_analisis_grupos_ficha_datos(client, db_session, crear_paciente):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Organización
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Grupos SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()
    org_id = org.id

    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    # 3. Dimensión y pregunta F2
    dim = (
        db_session.query(Dimension)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(CuestionarioVersion.codigo != "FICHA_DATOS")
        .first()
    )
    assert dim is not None, "Se requiere una dimensión de cuestionario evaluativo"

    pregunta_f2 = (
        db_session.query(Pregunta)
        .join(Dimension, Pregunta.dimension_id == Dimension.id)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(CuestionarioVersion.codigo == "FICHA_DATOS", Pregunta.codigo == "F2")
        .first()
    )
    assert pregunta_f2 is not None, "La pregunta F2 de FICHA_DATOS debe existir"

    # 4. Crear Evaluación
    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        organizacion_id=org_id,
        evaluador_id=admin_user.id,
        nombre="Evaluación Grupos Ficha 2026",
    )
    db_session.add(evaluacion)
    db_session.commit()

    def _crear_participante(sexo, nivel_riesgo):
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
            dimension_id=dim.id,
            puntaje_bruto=50.0,
            puntaje_transformado=50.0,
            nivel=nivel_riesgo,
        )
        db_session.add(res_dim)

        resp = Respuesta(
            id=uuid.uuid4(),
            participante_id=part.id,
            pregunta_id=pregunta_f2.id,
            valor_cifrado=cifrar_json(sexo),
        )
        db_session.add(resp)

    # 5 participantes FEMENINO (3 ALTO, 1 MUY_ALTO, 1 BAJO)
    for nivel in ["ALTO", "ALTO", "ALTO", "MUY_ALTO", "BAJO"]:
        _crear_participante("FEMENINO", nivel)

    # 3 participantes MASCULINO (2 BAJO, 1 MEDIO)
    for nivel in ["BAJO", "BAJO", "MEDIO"]:
        _crear_participante("MASCULINO", nivel)

    db_session.commit()

    # Consulta con variable sexo
    res = client.get(f"/api/indicadores/grupos?organizacion_id={org_id}&variable=sexo", headers=headers_admin)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["variable"] == "sexo"
    assert data["minimoAnonimato"] == 5

    # 1. Grupo "Femenino" presente con 5 participantes y 80.0% alto/muy alto
    grupos_por_nombre = {g["nombre"]: g for g in data["grupos"]}
    assert "Femenino" in grupos_por_nombre
    g_fem = grupos_por_nombre["Femenino"]
    assert g_fem["participantes"] == 5
    assert g_fem["porcentajeAltoMuyAlto"] == 80.0

    # 2. 3 participantes MASCULINO no aparecen y gruposOcultos es 1
    assert "Masculino" not in grupos_por_nombre
    assert data["gruposOcultos"] == 1

    # 3. Variable inválida responde 400
    res_invalida = client.get(f"/api/indicadores/grupos?organizacion_id={org_id}&variable=inexistente", headers=headers_admin)
    assert res_invalida.status_code == 400
