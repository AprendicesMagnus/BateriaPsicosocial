import uuid

import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.evaluation import Informe
from app.models.organization import Organizacion

PASSWORD_EVALUADOR = "Evaluador1234"
PASSWORD_PACIENTE = "Paciente1234"


def _encabezados(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_organizacion(client, headers_admin, nombre):
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": nombre, "nit": nit})
    assert res.status_code in (200, 201), res.text
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
    assert res.status_code in (200, 201), res.text
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
def escenario(client, db_session, crear_paciente):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, res.text
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    org_a = _crear_organizacion(client, headers_admin, "Organizacion A Acceso")
    org_b = _crear_organizacion(client, headers_admin, "Organizacion B Acceso")

    evaluador_a_id, email_evaluador_a = _crear_usuario(
        client, headers_admin, "EVALUADOR_SST", org_a, PASSWORD_EVALUADOR
    )
    _, email_evaluador_b = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org_b, PASSWORD_EVALUADOR)

    # El rol TRABAJADOR ya no existe: el participante es un PACIENTE con login.
    paciente_a_id, email_paciente_a = crear_paciente(org_a, password=PASSWORD_PACIENTE)

    res = client.get("/api/cuestionarios", headers=headers_admin)
    assert res.status_code == 200, res.text
    version_id = res.json()[0]["id"]

    res = client.post(
        "/api/evaluaciones",
        headers=headers_admin,
        json={
            "organizacionId": org_a,
            "nombre": "Evaluacion Acceso Organizacion A",
            "versionId": version_id,
            "trabajadoresIds": [str(paciente_a_id)],
        },
    )
    assert res.status_code in (200, 201), res.text
    evaluacion_a_id = uuid.UUID(res.json()["id"])

    informe_agrupado = _registrar_informe(db_session, evaluacion_a_id, "AGRUPADO", evaluador_a_id)
    informe_individual = _registrar_informe(
        db_session, evaluacion_a_id, "INDIVIDUAL", evaluador_a_id, trabajador_id=paciente_a_id
    )

    return {
        "evaluacion_a_id": str(evaluacion_a_id),
        "informe_agrupado_id": str(informe_agrupado.id),
        "informe_individual_id": str(informe_individual.id),
        "headers_admin": headers_admin,
        "headers_evaluador_a": _encabezados(client, email_evaluador_a, PASSWORD_EVALUADOR),
        "headers_evaluador_b": _encabezados(client, email_evaluador_b, PASSWORD_EVALUADOR),
        "headers_paciente_a": _encabezados(client, email_paciente_a, PASSWORD_PACIENTE),
    }


def _ids(respuesta):
    assert respuesta.status_code == 200, respuesta.text
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
    assert res.status_code == 200, res.text
    assert res.json() == []


def test_paciente_no_puede_listar_informes(client, escenario):
    # listar_informes responde 403 a cualquier rol no contemplado, incluido PACIENTE.
    res = client.get("/api/informes", headers=escenario["headers_paciente_a"])
    assert res.status_code == 403, res.text


def test_listado_requiere_autenticacion(client):
    assert client.get("/api/informes").status_code == 401


def test_evaluador_no_puede_generar_informes_de_otra_organizacion(client, escenario):
    headers = escenario["headers_evaluador_b"]

    res_agrupado = client.post(
        "/api/informes/agrupado",
        headers=headers,
        json={"evaluacionId": escenario["evaluacion_a_id"]},
    )
    assert res_agrupado.status_code == 403, res_agrupado.text

    res_individual = client.post(
        "/api/informes/individual",
        headers=headers,
        json={"evaluacionId": escenario["evaluacion_a_id"], "participanteId": str(uuid.uuid4())},
    )
    assert res_individual.status_code == 403, res_individual.text


def test_generar_informe_de_evaluacion_inexistente_retorna_404(client, escenario):
    res = client.post(
        "/api/informes/agrupado",
        headers=escenario["headers_evaluador_a"],
        json={"evaluacionId": str(uuid.uuid4())},
    )
    assert res.status_code == 404, res.text


def test_evaluador_no_puede_descargar_informe_de_otra_organizacion(client, escenario):
    res = client.get(
        f"/api/informes/{escenario['informe_agrupado_id']}/descargar",
        headers=escenario["headers_evaluador_b"],
    )
    assert res.status_code == 403, res.text


PASSWORD_JEFE = "Jefe1234"


def _preparar_jefe(client, db_session, escenario, es_creador):
    informe = db_session.query(Informe).filter(Informe.id == uuid.UUID(escenario["informe_agrupado_id"])).first()
    org_id = informe.evaluacion.organizacion_id
    jefe_id, email = _crear_usuario(client, escenario["headers_admin"], "JEFE", str(org_id), PASSWORD_JEFE)
    if es_creador:
        org = db_session.query(Organizacion).filter(Organizacion.id == org_id).first()
        org.creada_por_id = jefe_id
        db_session.commit()
    return _encabezados(client, email, PASSWORD_JEFE)


def test_jefe_creador_lista_solo_informes_agrupados_de_su_empresa(client, db_session, escenario):
    headers = _preparar_jefe(client, db_session, escenario, es_creador=True)
    ids = _ids(client.get("/api/informes", headers=headers))
    assert escenario["informe_agrupado_id"] in ids
    assert escenario["informe_individual_id"] not in ids


def test_jefe_creador_supera_la_autorizacion_de_descarga_de_informe_agrupado(client, db_session, escenario):
    headers = _preparar_jefe(client, db_session, escenario, es_creador=True)
    # El archivo no existe en el almacenamiento de pruebas: 404 (y no 403) indica que la autorizacion paso.
    res = client.get(f"/api/informes/{escenario['informe_agrupado_id']}/descargar", headers=headers)
    assert res.status_code == 404, res.text


def test_jefe_creador_no_puede_descargar_informe_individual(client, db_session, escenario):
    headers = _preparar_jefe(client, db_session, escenario, es_creador=True)
    res = client.get(f"/api/informes/{escenario['informe_individual_id']}/descargar", headers=headers)
    assert res.status_code == 403, res.text


def test_jefe_creador_pasa_la_validacion_de_rol_al_generar_informe_agrupado(client, db_session, escenario):
    headers = _preparar_jefe(client, db_session, escenario, es_creador=True)
    res = client.post(
        "/api/informes/agrupado",
        headers=headers,
        json={"evaluacionId": escenario["evaluacion_a_id"]},
    )
    # Llega al servicio: con menos del minimo de participantes responde 400 por anonimato, no 403 por rol.
    assert res.status_code == 400, res.text
    error_msg = res.json().get("error", "").lower()
    assert "anonimato" in error_msg or "mínimo" in error_msg


def test_jefe_que_no_creo_la_empresa_no_lista_descarga_ni_genera_informes(client, db_session, escenario):
    headers = _preparar_jefe(client, db_session, escenario, es_creador=False)

    ids = _ids(client.get("/api/informes", headers=headers))
    assert escenario["informe_agrupado_id"] not in ids

    res_descarga = client.get(f"/api/informes/{escenario['informe_agrupado_id']}/descargar", headers=headers)
    assert res_descarga.status_code == 403, res_descarga.text

    res_genera = client.post(
        "/api/informes/agrupado",
        headers=headers,
        json={"evaluacionId": escenario["evaluacion_a_id"]},
    )
    assert res_genera.status_code == 403, res_genera.text


def test_evaluador_de_la_organizacion_supera_la_autorizacion_de_descarga(client, escenario):
    # El archivo no existe en el almacenamiento de pruebas, por lo que se espera 404 y no 403.
    res = client.get(
        f"/api/informes/{escenario['informe_agrupado_id']}/descargar",
        headers=escenario["headers_evaluador_a"],
    )
    assert res.status_code == 404, res.text