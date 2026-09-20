import uuid

import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.evaluation import Informe

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


def _crear_usuario(client, headers_admin, rol_codigo, organizacion_id, password):
    email = f"{rol_codigo.lower()}_{uuid.uuid4().hex[:8]}@test.com"
    res = client.post(
        "/api/usuarios",
        headers=headers_admin,
        json={
            "nombre": "Prueba",
            "apellido": "Acceso",
            "email": email,
            "password": password,
            "rolCodigo": rol_codigo,
            "organizacionId": organizacion_id,
        },
    )
    assert res.status_code in (200, 201)
    return uuid.UUID(res.json()["id"]), email


def _registrar_informe(db, evaluacion_id, tipo, generado_por, trabajador_id=None):
    informe = Informe(
        evaluacion_id=evaluacion_id,
        tipo=tipo,
        formato="PDF",
        trabajador_id=trabajador_id,
        ruta_archivo=f"storage/informes/inexistente_{uuid.uuid4().hex}.pdf",
        generado_por=generado_por,
        anonimizado=tipo == "AGRUPADO",
    )
    db.add(informe)
    db.commit()
    db.refresh(informe)
    return informe


@pytest.fixture
def escenario(client, db_session):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    org_a = _crear_organizacion(client, headers_admin, "Organizacion A Acceso")
    org_b = _crear_organizacion(client, headers_admin, "Organizacion B Acceso")

    evaluador_a_id, email_evaluador_a = _crear_usuario(
        client, headers_admin, "EVALUADOR_SST", org_a, PASSWORD_EVALUADOR
    )
    _, email_evaluador_b = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_b, PASSWORD_EVALUADOR)
    trabajador_a_id, email_trabajador_a = _crear_usuario(
        client, headers_admin, "TRABAJADOR", org_a, PASSWORD_TRABAJADOR
    )

    version_id = client.get("/api/cuestionarios", headers=headers_admin).json()[0]["id"]
    res = client.post(
        "/api/evaluaciones",
        headers=headers_admin,
        json={
            "organizacionId": org_a,
            "nombre": "Evaluacion Acceso Organizacion A",
            "versionId": version_id,
            "trabajadoresIds": [str(trabajador_a_id)],
        },
    )
    assert res.status_code in (200, 201)
    evaluacion_a_id = uuid.UUID(res.json()["id"])

    informe_agrupado = _registrar_informe(db_session, evaluacion_a_id, "AGRUPADO", evaluador_a_id)
    informe_individual = _registrar_informe(
        db_session, evaluacion_a_id, "INDIVIDUAL", evaluador_a_id, trabajador_id=trabajador_a_id
    )

    return {
        "evaluacion_a_id": str(evaluacion_a_id),
        "informe_agrupado_id": str(informe_agrupado.id),
        "informe_individual_id": str(informe_individual.id),
        "headers_admin": headers_admin,
        "headers_evaluador_a": _encabezados(client, email_evaluador_a, PASSWORD_EVALUADOR),
        "headers_evaluador_b": _encabezados(client, email_evaluador_b, PASSWORD_EVALUADOR),
        "headers_trabajador_a": _encabezados(client, email_trabajador_a, PASSWORD_TRABAJADOR),
    }


def _ids(respuesta):
    assert respuesta.status_code == 200
    return {item["id"] for item in respuesta.json()}


def test_administrador_lista_informes_de_todas_las_organizaciones(client, escenario):
    ids = _ids(client.get("/api/informes", headers=escenario["headers_admin"]))
    assert escenario["informe_agrupado_id"] in ids
    assert escenario["informe_individual_id"] in ids


def test_evaluador_lista_informes_de_su_organizacion(client, escenario):
    ids = _ids(client.get("/api/informes", headers=escenario["headers_evaluador_a"]))
    assert escenario["informe_agrupado_id"] in ids
    assert escenario["informe_individual_id"] in ids


def test_evaluador_no_ve_informes_de_otra_organizacion(client, escenario):
    ids = _ids(client.get("/api/informes", headers=escenario["headers_evaluador_b"]))
    assert escenario["informe_agrupado_id"] not in ids
    assert escenario["informe_individual_id"] not in ids


def test_evaluador_no_filtra_informes_de_otra_organizacion_por_evaluacion(client, escenario):
    res = client.get(
        "/api/informes",
        headers=escenario["headers_evaluador_b"],
        params={"evaluacion_id": escenario["evaluacion_a_id"]},
    )
    assert res.status_code == 200
    assert res.json() == []


def test_trabajador_solo_lista_su_informe_individual(client, escenario):
    ids = _ids(client.get("/api/informes", headers=escenario["headers_trabajador_a"]))
    assert ids == {escenario["informe_individual_id"]}


def test_listado_requiere_autenticacion(client):
    assert client.get("/api/informes").status_code == 401


def test_evaluador_no_puede_generar_informes_de_otra_organizacion(client, escenario):
    headers = escenario["headers_evaluador_b"]

    res_agrupado = client.post(
        "/api/informes/agrupado",
        headers=headers,
        json={"evaluacionId": escenario["evaluacion_a_id"]},
    )
    assert res_agrupado.status_code == 403

    res_individual = client.post(
        "/api/informes/individual",
        headers=headers,
        json={"evaluacionId": escenario["evaluacion_a_id"], "participanteId": str(uuid.uuid4())},
    )
    assert res_individual.status_code == 403


def test_generar_informe_de_evaluacion_inexistente_retorna_404(client, escenario):
    res = client.post(
        "/api/informes/agrupado",
        headers=escenario["headers_evaluador_a"],
        json={"evaluacionId": str(uuid.uuid4())},
    )
    assert res.status_code == 404


def test_evaluador_no_puede_descargar_informe_de_otra_organizacion(client, escenario):
    res = client.get(
        f"/api/informes/{escenario['informe_agrupado_id']}/descargar",
        headers=escenario["headers_evaluador_b"],
    )
    assert res.status_code == 403


def test_evaluador_de_la_organizacion_supera_la_autorizacion_de_descarga(client, escenario):
    # El archivo no existe en el almacenamiento de pruebas, por lo que se espera 404 y no 403.
    res = client.get(
        f"/api/informes/{escenario['informe_agrupado_id']}/descargar",
        headers=escenario["headers_evaluador_a"],
    )
    assert res.status_code == 404
