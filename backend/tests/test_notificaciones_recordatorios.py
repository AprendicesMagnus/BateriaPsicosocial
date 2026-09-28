from unittest.mock import patch
import uuid
import pytest
from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import EvaluacionParticipante


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


@patch("app.services.notificaciones.enviar_correo")
def test_enviar_recordatorios_flujo_completo(mock_enviar_correo, client, db_session):
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Org y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa Recordatorios SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Ventas"})
    area_id = res_area.json()["id"]

    # 3. Crear 2 Trabajadores
    # Trab 1: Evaluación Pendiente
    email_p1 = f"pendiente_{uuid.uuid4().hex[:5]}@test.com"
    res_t1 = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Carlos",
        "apellido": "Pendiente",
        "email": email_p1,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Asesor Ventas"
    })
    t1_id = res_t1.json()["id"]

    # Trab 2: Evaluación Completada
    email_p2 = f"completado_{uuid.uuid4().hex[:5]}@test.com"
    res_t2 = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Maria",
        "apellido": "Completada",
        "email": email_p2,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Jefa Ventas"
    })
    t2_id = res_t2.json()["id"]

    # 4. Crear e Iniciar Evaluación
    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Recordatorios 2026",
        "trabajadoresIds": [t1_id, t2_id]
    })
    eval_id = res_eval.json()["id"]
    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    # 5. Completar evaluación para Trab 2 (Maria)
    res_login_t2 = client.post("/api/auth/login", json={"email": email_p2, "password": "Trabajador1234"})
    headers_t2 = {"Authorization": f"Bearer {res_login_t2.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_t2)

    # Completar Ficha y cuestionarios de t2
    client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_t2, json={
        "nombreCompleto": "Maria Completada",
        "sexo": "Femenino",
        "anioNacimiento": "1988",
        "estadoCivil": "Soltero (a)",
        "nivelEstudios": "Profesional",
        "ocupacion": "Administrador",
        "residenciaCiudad": "Bogotá",
        "residenciaDepartamento": "Cundinamarca",
        "estrato": "4",
        "tipoVivienda": "Propia",
        "personasACargo": 1,
        "trabajoCiudad": "Bogotá",
        "trabajoDepartamento": "Cundinamarca",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "5",
        "nombreCargo": "Jefa Ventas",
        "tipoCargo": "Jefatura - tiene personal a cargo",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "3",
        "areaODepartamento": "Ventas",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    })

    # Marcar directamente a t2 como COMPLETADA en la BD para evitar 185 llamadas HTTP lentas
    p2 = db_session.query(EvaluacionParticipante).filter(
        EvaluacionParticipante.evaluacion_id == eval_id,
        EvaluacionParticipante.trabajador_id == t2_id
    ).first()
    p2.estado = "COMPLETADA"
    db_session.commit()

    # Confirmar t2 completada
    eval_det = client.get(f"/api/evaluaciones/{eval_id}", headers=headers_admin).json()
    p2_det = next(p for p in eval_det["detalleParticipantes"] if p["trabajadorId"] == t2_id)
    assert p2_det["estado"] == "COMPLETADA"

    # 6. PRIMER DISPARO DE RECORDATORIOS (a) y (c):
    # Debe enviar recordatorio a t1 (pendiente) y NO a t2 (completado)
    res_rec1 = client.post("/api/notificaciones/enviar-recordatorios", headers=headers_admin)
    assert res_rec1.status_code == 200
    data_rec1 = res_rec1.json()
    t1_det1 = next((d for d in data_rec1["detalles"] if d["trabajadorId"] == t1_id), None)
    t2_det1 = next((d for d in data_rec1["detalles"] if d["trabajadorId"] == t2_id), None)
    assert t1_det1 is not None, "El trabajador 1 pendiente debió recibir un recordatorio."
    assert t1_det1["estadoNotificacion"] == "ENVIADA"
    assert t2_det1 is None, "El trabajador 2 completado NO debió recibir ningún recordatorio."

    # Verificar que t1 recibió la notificación en su bandeja
    res_login_t1 = client.post("/api/auth/login", json={"email": email_p1, "password": "Trabajador1234"})
    headers_t1 = {"Authorization": f"Bearer {res_login_t1.json()['token']}"}
    res_notis1 = client.get("/api/notificaciones", headers=headers_t1)
    assert res_notis1.status_code == 200
    notis_t1 = res_notis1.json()
    assert any(n["tipo"] == "RECORDATORIO_EVALUACION" for n in notis_t1)

    # 7. SEGUNDO DISPARO INMEDIATO DE RECORDATORIOS (b) IDEMPOTENCIA:
    # No debe duplicar notificación para t1 porque ya se le envió en las últimas 24h
    res_rec2 = client.post("/api/notificaciones/enviar-recordatorios", headers=headers_admin)
    assert res_rec2.status_code == 200
    data_rec2 = res_rec2.json()
    t1_det2 = next((d for d in data_rec2["detalles"] if d["trabajadorId"] == t1_id), None)
    assert t1_det2 is not None, "El trabajador 1 debió evaluarse para idempotencia."
    assert t1_det2["estadoNotificacion"] == "OMITIDA_RECIENTE"
