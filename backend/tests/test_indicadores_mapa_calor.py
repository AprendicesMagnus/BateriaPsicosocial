import uuid
import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Area, Organizacion
from app.models.survey import CuestionarioVersion, Dimension


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_mapa_calor_areas_y_dimensiones(client, db_session, crear_paciente):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Organización y Áreas
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Mapa Calor SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()
    org_id = org.id

    area_ops = Area(id=uuid.uuid4(), organizacion_id=org_id, nombre="Operaciones")
    area_admin = Area(id=uuid.uuid4(), organizacion_id=org_id, nombre="Administración")
    db_session.add_all([area_ops, area_admin])
    db_session.commit()

    # Dimensión y cuestionario de prueba
    dim = db_session.query(Dimension).first()
    assert dim is not None, "Debe existir al menos una dimensión sembrada"
    cuestionario = db_session.query(CuestionarioVersion).filter(CuestionarioVersion.id == dim.version_id).first()
    assert cuestionario is not None, "Debe existir la versión del cuestionario correspondiente"

    # 3. Participantes para Área Operaciones (5 participantes: 3 ALTO, 1 MUY_ALTO, 1 MEDIO)
    niveles_ops = ["ALTO", "ALTO", "ALTO", "MUY_ALTO", "MEDIO"]
    participantes_ops_ids = [crear_paciente(org_id, area_id=area_ops.id)[0] for _ in range(5)]

    # 4. Participantes para Área Administración (3 participantes: 2 BAJO, 1 MEDIO)
    niveles_admin = ["BAJO", "BAJO", "MEDIO"]
    participantes_admin_ids = [crear_paciente(org_id, area_id=area_admin.id)[0] for _ in range(3)]

    # 5. Participantes sin área asignada (5 participantes: 5 BAJO)
    participantes_sin_area_ids = [crear_paciente(org_id, area_id=None)[0] for _ in range(5)]

    from app.models.user import Usuario
    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    # Crear Evaluación
    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        organizacion_id=org_id,
        evaluador_id=admin_user.id,
        nombre="Evaluación Mapa Calor 2026",
    )
    db_session.add(evaluacion)
    db_session.commit()

    def _crear_participante_con_resultado(trabajador_id, nivel):
        part = EvaluacionParticipante(
            id=uuid.uuid4(),
            evaluacion_id=evaluacion.id,
            trabajador_id=trabajador_id,
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

    for trabajador_id, nivel in zip(participantes_ops_ids, niveles_ops):
        _crear_participante_con_resultado(trabajador_id, nivel)

    for trabajador_id, nivel in zip(participantes_admin_ids, niveles_admin):
        _crear_participante_con_resultado(trabajador_id, nivel)

    for trabajador_id in participantes_sin_area_ids:
        _crear_participante_con_resultado(trabajador_id, "BAJO")

    db_session.commit()

    # 6. Consultar endpoint
    res = client.get(
        f"/api/indicadores/mapa-calor?organizacion_id={org_id}&codigo={cuestionario.codigo}",
        headers=headers_admin,
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["codigo"] == cuestionario.codigo
    assert data["minimoAnonimato"] == 5

    areas_por_nombre = {a["nombre"]: a for a in data["areas"]}

    # Caso 1: Área Operaciones con 5 participantes -> anonimizado False, total 5, nivel "ALTO", porcentajeAltoMuyAlto 80.0
    assert "Operaciones" in areas_por_nombre
    celda_ops = areas_por_nombre["Operaciones"]["celdas"][dim.codigo]
    assert celda_ops["anonimizado"] is False
    assert celda_ops["total"] == 5
    assert celda_ops["nivel"] == "ALTO"
    assert celda_ops["porcentajeAltoMuyAlto"] == 80.0

    # Caso 2: Área Administración con 3 participantes -> exactamente {"anonimizado": True}
    assert "Administración" in areas_por_nombre
    celda_admin = areas_por_nombre["Administración"]["celdas"][dim.codigo]
    assert celda_admin == {"anonimizado": True}

    # Caso 3: Participantes sin área aparecen en fila "Sin área asignada"
    assert "Sin área asignada" in areas_por_nombre
    celda_sin_area = areas_por_nombre["Sin área asignada"]["celdas"][dim.codigo]
    assert celda_sin_area["anonimizado"] is False
    assert celda_sin_area["total"] == 5
    assert celda_sin_area["nivel"] == "BAJO"
