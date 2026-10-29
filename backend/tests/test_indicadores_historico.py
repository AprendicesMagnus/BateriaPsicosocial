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


def test_obtener_historico_indicadores_cronologico(client, db_session, crear_paciente):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Org y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa Historico SAS", "nit": nit_rnd})
    assert res_org.status_code == 200, res_org.text
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Operaciones"})
    assert res_area.status_code == 200, res_area.text
    area_id = res_area.json()["id"]

    dim = db_session.query(Dimension).first()

    # 3. Evaluación con 1 participante: con el mínimo de anonimato en 1, ya es visible
    paciente_id_1, _ = crear_paciente(org_id, area_id=area_id)
    res_eval1 = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación BRP 2025",
        "trabajadoresIds": [str(paciente_id_1)],
    })
    assert res_eval1.status_code == 200, res_eval1.text
    eval1_id = res_eval1.json()["id"]

    p1 = db_session.query(EvaluacionParticipante).filter(
        EvaluacionParticipante.evaluacion_id == eval1_id,
        EvaluacionParticipante.trabajador_id == paciente_id_1,
    ).first()
    assert p1 is not None
    p1.estado = "COMPLETADA"
    db_session.add(ResultadoDimension(
        participante_id=p1.id,
        dimension_id=dim.id,
        puntaje_bruto=75.0,
        puntaje_transformado=75.0,
        nivel="ALTO",
    ))
    db_session.commit()

    # 4. Evaluación con 5 participantes: también visible
    ids_eval2 = [crear_paciente(org_id, area_id=area_id)[0] for _ in range(5)]
    res_eval2 = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación BRP 2026",
        "trabajadoresIds": [str(uid) for uid in ids_eval2],
    })
    assert res_eval2.status_code == 200, res_eval2.text
    eval2_id = res_eval2.json()["id"]

    for uid in ids_eval2:
        part = db_session.query(EvaluacionParticipante).filter(
            EvaluacionParticipante.evaluacion_id == eval2_id,
            EvaluacionParticipante.trabajador_id == uid,
        ).first()
        assert part is not None
        part.estado = "COMPLETADA"
        db_session.add(ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=25.0,
            puntaje_transformado=25.0,
            nivel="BAJO",
        ))
    db_session.commit()

    # 5. Consultar histórico comparativo para la organización
    res_hist = client.get(f"/api/indicadores/historico?organizacion_id={org_id}", headers=headers_admin)
    assert res_hist.status_code == 200, res_hist.text
    data_hist = res_hist.json()

    historico = data_hist["historico"]
    assert len(historico) == 2, f"Se esperaban 2 evaluaciones en el histórico, pero se obtuvieron {len(historico)}"
    assert "minimoAnonimato" in data_hist

    # Evaluación con 1 participante (>= mínimo de 1): visible con promedio
    eval_2025 = next(e for e in historico if e["nombreEvaluacion"] == "Evaluación BRP 2025")
    assert eval_2025["oculto"] is False
    assert eval_2025["promedioPuntajeTransformado"] is not None
    assert eval_2025["distribucionNiveles"] is not None

    # Evaluación con 5 participantes (>= mínimo): también visible con promedio
    eval_2026 = next(e for e in historico if e["nombreEvaluacion"] == "Evaluación BRP 2026")
    assert eval_2026["oculto"] is False
    assert eval_2026["promedioPuntajeTransformado"] is not None
    assert eval_2026["distribucionNiveles"] is not None