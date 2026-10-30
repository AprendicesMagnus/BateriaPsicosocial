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


def test_comparar_dos_evaluaciones(client, db_session, crear_paciente):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Org y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa Comparar SAS", "nit": nit_rnd})
    assert res_org.status_code == 200, res_org.text
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Operaciones"})
    assert res_area.status_code == 200, res_area.text
    area_id = res_area.json()["id"]

    dim = db_session.query(Dimension).first()
    assert dim is not None

    # 3. Evaluacion A con 5 participantes completados (promedio 40.0)
    ids_eval_a = [crear_paciente(org_id, area_id=area_id)[0] for _ in range(5)]
    res_eval_a = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Diagnóstica 2024",
        "trabajadoresIds": [str(uid) for uid in ids_eval_a],
    })
    assert res_eval_a.status_code == 200, res_eval_a.text
    eval_a_id = res_eval_a.json()["id"]

    for uid in ids_eval_a:
        part = db_session.query(EvaluacionParticipante).filter(
            EvaluacionParticipante.evaluacion_id == eval_a_id,
            EvaluacionParticipante.trabajador_id == uid,
        ).first()
        part.estado = "COMPLETADA"
        db_session.add(ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=40.0,
            puntaje_transformado=40.0,
            nivel="MEDIO",
        ))
    db_session.commit()

    # 4. Evaluacion B con 5 participantes completados (promedio 55.0)
    ids_eval_b = [crear_paciente(org_id, area_id=area_id)[0] for _ in range(5)]
    res_eval_b = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Seguimiento 2025",
        "trabajadoresIds": [str(uid) for uid in ids_eval_b],
    })
    assert res_eval_b.status_code == 200, res_eval_b.text
    eval_b_id = res_eval_b.json()["id"]

    for uid in ids_eval_b:
        part = db_session.query(EvaluacionParticipante).filter(
            EvaluacionParticipante.evaluacion_id == eval_b_id,
            EvaluacionParticipante.trabajador_id == uid,
        ).first()
        part.estado = "COMPLETADA"
        db_session.add(ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=55.0,
            puntaje_transformado=55.0,
            nivel="ALTO",
        ))
    db_session.commit()

    # 5. Evaluacion C con solo 2 participantes (< minimo de 5)
    ids_eval_c = [crear_paciente(org_id, area_id=area_id)[0] for _ in range(2)]
    res_eval_c = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Piloto 2026",
        "trabajadoresIds": [str(uid) for uid in ids_eval_c],
    })
    assert res_eval_c.status_code == 200, res_eval_c.text
    eval_c_id = res_eval_c.json()["id"]

    for uid in ids_eval_c:
        part = db_session.query(EvaluacionParticipante).filter(
            EvaluacionParticipante.evaluacion_id == eval_c_id,
            EvaluacionParticipante.trabajador_id == uid,
        ).first()
        part.estado = "COMPLETADA"
        db_session.add(ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=30.0,
            puntaje_transformado=30.0,
            nivel="BAJO",
        ))
    db_session.commit()

    # Caso (a): Comparar A y B (ambas >= 5 participantes)
    res_comp_ab = client.get(
        f"/api/indicadores/comparar?evaluacion_a={eval_a_id}&evaluacion_b={eval_b_id}&organizacion_id={org_id}",
        headers=headers_admin,
    )
    assert res_comp_ab.status_code == 200, res_comp_ab.text
    data_ab = res_comp_ab.json()

    assert len(data_ab["evaluaciones"]) == 2
    assert data_ab["evaluaciones"][0]["oculto"] is False
    assert data_ab["evaluaciones"][1]["oculto"] is False

    dim_target = next(d for d in data_ab["dimensiones"] if d["codigo"] == dim.codigo)
    assert dim_target["promedioA"] == 40.0
    assert dim_target["promedioB"] == 55.0
    assert dim_target["diferencia"] == 15.0

    # Caso (b): Comparar A y C (C tiene solo 2 participantes)
    res_comp_ac = client.get(
        f"/api/indicadores/comparar?evaluacion_a={eval_a_id}&evaluacion_b={eval_c_id}&organizacion_id={org_id}",
        headers=headers_admin,
    )
    assert res_comp_ac.status_code == 200, res_comp_ac.text
    data_ac = res_comp_ac.json()

    assert data_ac["evaluaciones"][0]["oculto"] is False
    assert data_ac["evaluaciones"][1]["oculto"] is True
    dim_target_c = next(d for d in data_ac["dimensiones"] if d["codigo"] == dim.codigo)
    assert dim_target_c["promedioA"] == 40.0
    assert dim_target_c["promedioB"] is None
    assert dim_target_c["diferencia"] is None

    # Caso (c): Misma evaluacion en A y B -> 400
    res_misma = client.get(
        f"/api/indicadores/comparar?evaluacion_a={eval_a_id}&evaluacion_b={eval_a_id}",
        headers=headers_admin,
    )
    assert res_misma.status_code == 400
    assert "distintas" in res_misma.text

    # Caso (d): Evaluacion inexistente -> 404
    id_fake = uuid.uuid4()
    res_404 = client.get(
        f"/api/indicadores/comparar?evaluacion_a={eval_a_id}&evaluacion_b={id_fake}",
        headers=headers_admin,
    )
    assert res_404.status_code == 404
    assert "no encontrada" in res_404.text

    # Caso (e): Usuario sin permiso (PACIENTE) -> 403
    _pid, p_email = crear_paciente(org_id, area_id=area_id, password="Paciente123!")
    res_login_p = client.post("/api/auth/login", json={"email": p_email, "password": "Paciente123!"})
    assert res_login_p.status_code == 200, res_login_p.text
    headers_paciente = {"Authorization": f"Bearer {res_login_p.json()['token']}"}

    res_403 = client.get(
        f"/api/indicadores/comparar?evaluacion_a={eval_a_id}&evaluacion_b={eval_b_id}",
        headers=headers_paciente,
    )
    assert res_403.status_code == 403
    assert "permisos" in res_403.text
