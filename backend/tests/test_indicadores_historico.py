import uuid
import pytest
from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import EvaluacionParticipante, ResultadoDimension
from app.models.survey import Dimension


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_obtener_historico_indicadores_cronologico(client, db_session):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Org y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa Historico SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Operaciones"})
    area_id = res_area.json()["id"]

    # 3. Crear Trabajador
    email_trab = f"trab_hist_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Elena",
        "apellido": "Historico",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Operaria"
    })
    t_id = res_trab.json()["id"]

    # 4. Crear y finalizar Evaluación 1 (Año 2025) con puntaje alto
    res_eval1 = client.post("/api/evaluaciones", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Evaluación BRP 2025", "trabajadoresIds": [t_id]})
    eval1_id = res_eval1.json()["id"]

    p1 = db_session.query(EvaluacionParticipante).filter(
        EvaluacionParticipante.evaluacion_id == eval1_id,
        EvaluacionParticipante.trabajador_id == t_id
    ).first()
    p1.estado = "COMPLETADA"

    dim = db_session.query(Dimension).first()
    res1 = ResultadoDimension(
        participante_id=p1.id,
        dimension_id=dim.id,
        puntaje_bruto=75.0,
        puntaje_transformado=75.0,
        nivel="ALTO"
    )
    db_session.add(res1)
    db_session.commit()

    # 5. Crear y finalizar Evaluación 2 (Año 2026) con puntaje bajo
    res_eval2 = client.post("/api/evaluaciones", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Evaluación BRP 2026", "trabajadoresIds": [t_id]})
    eval2_id = res_eval2.json()["id"]

    p2 = db_session.query(EvaluacionParticipante).filter(
        EvaluacionParticipante.evaluacion_id == eval2_id,
        EvaluacionParticipante.trabajador_id == t_id
    ).first()
    p2.estado = "COMPLETADA"

    res2 = ResultadoDimension(
        participante_id=p2.id,
        dimension_id=dim.id,
        puntaje_bruto=25.0,
        puntaje_transformado=25.0,
        nivel="BAJO"
    )
    db_session.add(res2)
    db_session.commit()

    # 6. Consultar histórico comparativo para la organización
    res_hist = client.get(f"/api/indicadores/historico?organizacion_id={org_id}", headers=headers_admin)
    assert res_hist.status_code == 200
    data_hist = res_hist.json()

    historico = data_hist["historico"]
    assert len(historico) == 2, f"Se esperaban 2 evaluaciones en el histórico, pero se obtuvieron {len(historico)}"

    # Verificar orden cronológico y que el promedio cambió entre 2025 y 2026
    assert historico[0]["nombreEvaluacion"] == "Evaluación BRP 2025"
    assert historico[1]["nombreEvaluacion"] == "Evaluación BRP 2026"

    # En 2025 el puntaje fue mayor que en 2026 (mejora en nivel de riesgo)
    assert historico[0]["promedioPuntajeTransformado"] > historico[1]["promedioPuntajeTransformado"]
