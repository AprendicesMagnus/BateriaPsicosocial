import uuid
import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.organization import Area
from app.models.evaluation import EvaluacionParticipante

PASSWORD_EVALUADOR = "Evaluador1234"
PASSWORD_TRABAJADOR = "Trabajador1234"


def _encabezados(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_organizacion(client, headers_admin, nombre):
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": nombre, "nit": nit})
    assert res.status_code in (200, 201)
    return res.json()["id"]


def _crear_usuario(client, headers_admin, rol_codigo, organizacion_id, password, area_id=None):
    email = f"{rol_codigo.lower()}_{uuid.uuid4().hex[:8]}@test.com"
    body = {
        "nombre": "Prueba",
        "apellido": "Reportes",
        "email": email,
        "password": password,
        "rolCodigo": rol_codigo,
        "organizacionId": organizacion_id,
    }
    if area_id:
        body["areaId"] = str(area_id)
    res = client.post("/api/usuarios", headers=headers_admin, json=body)
    assert res.status_code in (200, 201)
    return uuid.UUID(res.json()["id"]), email


@pytest.fixture
def escenario_reportes(client, db_session):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    org_a = _crear_organizacion(client, headers_admin, "Organizacion A Reportes")
    org_b = _crear_organizacion(client, headers_admin, "Organizacion B Reportes")

    # Crear área A (con 5 trabajadores completados -> listo)
    area_a = Area(organizacion_id=uuid.UUID(org_a), nombre=f"Area A Listo {uuid.uuid4().hex[:4]}")
    # Crear área B (con 2 trabajadores completados -> restringido)
    area_b = Area(organizacion_id=uuid.UUID(org_b), nombre=f"Area B Restringido {uuid.uuid4().hex[:4]}")
    db_session.add_all([area_a, area_b])
    db_session.commit()
    db_session.refresh(area_a)
    db_session.refresh(area_b)

    evaluador_a_id, email_evaluador_a = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_a, PASSWORD_EVALUADOR)
    _, email_evaluador_b = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_b, PASSWORD_EVALUADOR)
    trabajador_a_id, email_trabajador_a = _crear_usuario(client, headers_admin, "TRABAJADOR", org_a, PASSWORD_TRABAJADOR, area_id=area_a.id)

    # Crear evaluación en Org A
    version_id = client.get("/api/cuestionarios", headers=headers_admin).json()[0]["id"]
    res_ev_a = client.post(
        "/api/evaluaciones",
        headers=headers_admin,
        json={
            "organizacionId": org_a,
            "nombre": "Evaluacion Reportes Org A",
            "versionId": version_id,
            "trabajadoresIds": [str(trabajador_a_id)],
        },
    )
    assert res_ev_a.status_code in (200, 201)
    evaluacion_a_id = uuid.UUID(res_ev_a.json()["id"])

    # Crear 5 trabajadores en Area A y registrarlos completados
    for i in range(5):
        t_id, _ = _crear_usuario(client, headers_admin, "TRABAJADOR", org_a, PASSWORD_TRABAJADOR, area_id=area_a.id)
        part = EvaluacionParticipante(evaluacion_id=evaluacion_a_id, trabajador_id=t_id, estado="COMPLETADA")
        db_session.add(part)
    
    # Crear 2 trabajadores en Area B con evaluación en Org B y registrarlos completados
    res_ev_b = client.post(
        "/api/evaluaciones",
        headers=headers_admin,
        json={
            "organizacionId": org_b,
            "nombre": "Evaluacion Reportes Org B",
            "versionId": version_id,
            "trabajadoresIds": [],
        },
    )
    evaluacion_b_id = uuid.UUID(res_ev_b.json()["id"])
    for i in range(2):
        t_id, _ = _crear_usuario(client, headers_admin, "TRABAJADOR", org_b, PASSWORD_TRABAJADOR, area_id=area_b.id)
        part = EvaluacionParticipante(evaluacion_id=evaluacion_b_id, trabajador_id=t_id, estado="COMPLETADA")
        db_session.add(part)

    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "area_a_id": str(area_a.id),
        "area_b_id": str(area_b.id),
        "headers_admin": headers_admin,
        "headers_evaluador_a": _encabezados(client, email_evaluador_a, PASSWORD_EVALUADOR),
        "headers_evaluador_b": _encabezados(client, email_evaluador_b, PASSWORD_EVALUADOR),
        "headers_trabajador_a": _encabezados(client, email_trabajador_a, PASSWORD_TRABAJADOR),
    }


def test_administrador_lista_reportes_todas_organizaciones(client, escenario_reportes):
    res = client.get("/api/reportes", headers=escenario_reportes["headers_admin"])
    assert res.status_code == 200
    ids = {item["id"] for item in res.json()}
    assert escenario_reportes["area_a_id"] in ids
    assert escenario_reportes["area_b_id"] in ids


def test_evaluador_solo_lista_reportes_su_organizacion(client, escenario_reportes):
    res_a = client.get("/api/reportes", headers=escenario_reportes["headers_evaluador_a"])
    assert res_a.status_code == 200
    ids_a = {item["id"] for item in res_a.json()}
    assert escenario_reportes["area_a_id"] in ids_a
    assert escenario_reportes["area_b_id"] not in ids_a

    res_b = client.get("/api/reportes", headers=escenario_reportes["headers_evaluador_b"])
    assert res_b.status_code == 200
    ids_b = {item["id"] for item in res_b.json()}
    assert escenario_reportes["area_b_id"] in ids_b
    assert escenario_reportes["area_a_id"] not in ids_b


def test_area_con_5_o_mas_completados_es_listo(client, escenario_reportes):
    res = client.get("/api/reportes", headers=escenario_reportes["headers_evaluador_a"])
    assert res.status_code == 200
    item_a = next(item for item in res.json() if item["id"] == escenario_reportes["area_a_id"])
    assert item_a["estado"] == "listo"
    assert item_a["participantesCompletados"] >= 5


def test_area_menos_de_5_completados_es_restringido(client, escenario_reportes):
    res = client.get("/api/reportes", headers=escenario_reportes["headers_evaluador_b"])
    assert res.status_code == 200
    item_b = next(item for item in res.json() if item["id"] == escenario_reportes["area_b_id"])
    assert item_b["estado"] == "restringido"
    assert item_b["participantesCompletados"] < 5


def test_reportes_requiere_autenticacion(client):
    assert client.get("/api/reportes").status_code == 401


def test_trabajador_sin_acceso_reportes(client, escenario_reportes):
    res = client.get("/api/reportes", headers=escenario_reportes["headers_trabajador_a"])
    assert res.status_code == 403
