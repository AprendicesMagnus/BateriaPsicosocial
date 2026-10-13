"""
guardar_respuesta solo debe aceptar preguntas de los instrumentos asignados al participante.

Un invitado del enlace publico no tiene asignado el Intralaboral hasta que guarda la
Ficha de Datos (la forma A o B se asigna segun el tipo de cargo).
"""
import uuid

import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.survey import CuestionarioVersion, Dimension, Pregunta


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


@pytest.fixture
def participante_enlace(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200, res.text
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post(
        "/api/organizaciones",
        headers=headers_admin,
        json={"nombre": "Empresa Pertenencia SAS", "nit": nit},
    )
    assert res_org.status_code in (200, 201), res_org.text
    org_id = res_org.json()["id"]

    email_eval = f"eval_pertenencia_{uuid.uuid4().hex[:8]}@test.com"
    res_user = client.post(
        "/api/usuarios",
        headers=headers_admin,
        json={
            "nombre": "Eva",
            "apellido": "Pertenencia",
            "email": email_eval,
            "password": "Evaluador1234",
            "rolCodigo": "EVALUADOR_SST",
            "organizacionId": org_id,
        },
    )
    assert res_user.status_code in (200, 201), res_user.text

    res_login = client.post(
        "/api/auth/login",
        json={"email": email_eval, "password": "Evaluador1234"},
    )
    assert res_login.status_code == 200, res_login.text
    headers_eval = {"Authorization": f"Bearer {res_login.json()['token']}"}

    res_enlace = client.post(
        "/api/enlaces",
        headers=headers_eval,
        json={"nombre": "Prueba de pertenencia"},
    )
    assert res_enlace.status_code in (200, 201), res_enlace.text

    res_inicio = client.post(
        f"/api/enlaces/publico/{res_enlace.json()['token']}/iniciar",
        json={"aceptaConsentimiento": True},
    )
    assert res_inicio.status_code in (200, 201), res_inicio.text
    datos = res_inicio.json()

    headers = {"Authorization": f"Bearer {datos['token']}"}
    eval_id = datos["evaluacionId"]

    res_preg = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers)
    assert res_preg.status_code == 200, res_preg.text
    preguntas = res_preg.json()["preguntas"]
    assert preguntas, "El cuestionario pendiente no contiene preguntas."

    return {"eval_id": eval_id, "headers": headers, "preguntas": preguntas}


def test_pregunta_de_instrumento_no_asignado_es_rechazada(
    client, db_session, participante_enlace
):
    pregunta_ajena = (
        db_session.query(Pregunta)
        .join(Dimension, Pregunta.dimension_id == Dimension.id)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(CuestionarioVersion.codigo == "INTRALABORAL_A")
        .first()
    )
    assert pregunta_ajena is not None, "El Intralaboral A no esta sembrado."

    res = client.post(
        f"/api/evaluaciones/{participante_enlace['eval_id']}/respuestas",
        headers=participante_enlace["headers"],
        json={"pregunta_codigo": pregunta_ajena.codigo, "valor": 3},
    )

    assert res.status_code == 400, res.text


def test_pregunta_del_instrumento_pendiente_sigue_aceptandose(client, participante_enlace):
    codigo = participante_enlace["preguntas"][0]["codigo"]

    res = client.post(
        f"/api/evaluaciones/{participante_enlace['eval_id']}/respuestas",
        headers=participante_enlace["headers"],
        json={"pregunta_codigo": codigo, "valor": 3},
    )

    assert res.status_code == 200, res.text