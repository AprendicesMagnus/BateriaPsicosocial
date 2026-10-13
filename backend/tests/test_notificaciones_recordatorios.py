import uuid
from unittest.mock import patch

import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import EvaluacionParticipante

PASSWORD_PACIENTE = "Trabajador1234"


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


@pytest.fixture
def headers_admin(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


@pytest.fixture
def organizacion(client, headers_admin):
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"

    res_org = client.post(
        "/api/organizaciones",
        headers=headers_admin,
        json={"nombre": "Empresa Recordatorios SAS", "nit": nit},
    )
    assert res_org.status_code in (200, 201), res_org.text
    org_id = res_org.json()["id"]

    res_area = client.post(
        "/api/organizaciones/areas",
        headers=headers_admin,
        json={"organizacionId": org_id, "nombre": "Ventas"},
    )
    assert res_area.status_code in (200, 201), res_area.text
    return {"org_id": org_id, "area_id": res_area.json()["id"]}


def _crear_evaluacion_en_curso(client, headers_admin, org_id, usuarios_ids, nombre):
    res_eval = client.post(
        "/api/evaluaciones",
        headers=headers_admin,
        json={
            "organizacionId": org_id,
            "nombre": nombre,
            "trabajadoresIds": [str(u) for u in usuarios_ids],
        },
    )
    assert res_eval.status_code in (200, 201), res_eval.text
    eval_id = res_eval.json()["id"]

    res_inicio = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)
    assert res_inicio.status_code == 200, res_inicio.text
    return eval_id


def _detalle_de(data, usuario_id):
    return next(
        (d for d in data["detalles"] if d["trabajadorId"] == str(usuario_id)),
        None,
    )


@patch("app.services.notificaciones.enviar_correo")
def test_enviar_recordatorios_flujo_completo(
    mock_enviar_correo, client, db_session, headers_admin, organizacion, crear_paciente
):
    org_id = organizacion["org_id"]
    area_id = organizacion["area_id"]

    # t1: evaluacion pendiente. t2: evaluacion completada.
    t1_id, email_t1 = crear_paciente(org_id, area_id, password=PASSWORD_PACIENTE)
    t2_id, _ = crear_paciente(org_id, area_id, password=PASSWORD_PACIENTE)

    eval_id = _crear_evaluacion_en_curso(
        client, headers_admin, org_id, [t1_id, t2_id], "Evaluacion Recordatorios 2026"
    )

    # Marcar a t2 como COMPLETADA directamente en la BD para evitar cientos de llamadas HTTP.
    p2 = (
        db_session.query(EvaluacionParticipante)
        .filter(
            EvaluacionParticipante.evaluacion_id == uuid.UUID(eval_id),
            EvaluacionParticipante.trabajador_id == t2_id,
        )
        .first()
    )
    assert p2 is not None, "t2 no quedo como participante de la evaluacion."
    p2.estado = "COMPLETADA"
    db_session.commit()

    res_det = client.get(f"/api/evaluaciones/{eval_id}", headers=headers_admin)
    assert res_det.status_code == 200, res_det.text
    p2_det = next(
        p for p in res_det.json()["detalleParticipantes"] if p["trabajadorId"] == str(t2_id)
    )
    assert p2_det["estado"] == "COMPLETADA"

    # Primer disparo: recordatorio a t1 (pendiente) y ninguno a t2 (completado).
    res_rec1 = client.post("/api/notificaciones/enviar-recordatorios", headers=headers_admin)
    assert res_rec1.status_code == 200, res_rec1.text
    data_rec1 = res_rec1.json()
    t1_det1 = _detalle_de(data_rec1, t1_id)
    t2_det1 = _detalle_de(data_rec1, t2_id)
    assert t1_det1 is not None, "El trabajador 1 pendiente debio recibir un recordatorio."
    assert t1_det1["estadoNotificacion"] == "ENVIADA"
    assert t2_det1 is None, "El trabajador 2 completado NO debio recibir ningun recordatorio."

    # t1 recibe la notificacion en su bandeja.
    res_login_t1 = client.post(
        "/api/auth/login", json={"email": email_t1, "password": PASSWORD_PACIENTE}
    )
    assert res_login_t1.status_code == 200, res_login_t1.text
    headers_t1 = {"Authorization": f"Bearer {res_login_t1.json()['token']}"}
    res_notis1 = client.get("/api/notificaciones", headers=headers_t1)
    assert res_notis1.status_code == 200, res_notis1.text
    assert any(n["tipo"] == "RECORDATORIO_EVALUACION" for n in res_notis1.json())

    # Segundo disparo inmediato: idempotencia, no se duplica la notificacion a t1.
    res_rec2 = client.post("/api/notificaciones/enviar-recordatorios", headers=headers_admin)
    assert res_rec2.status_code == 200, res_rec2.text
    t1_det2 = _detalle_de(res_rec2.json(), t1_id)
    assert t1_det2 is not None, "El trabajador 1 debio evaluarse para idempotencia."
    assert t1_det2["estadoNotificacion"] == "OMITIDA_RECIENTE"


@patch("app.services.notificaciones.enviar_correo")
def test_no_envia_recordatorios_a_pacientes_invitados_del_enlace(
    mock_enviar_correo, client, headers_admin, organizacion, crear_paciente
):
    org_id = organizacion["org_id"]
    area_id = organizacion["area_id"]

    # Control: paciente con login y evaluacion pendiente, debe recibir recordatorio.
    control_id, email_control = crear_paciente(org_id, area_id, password=PASSWORD_PACIENTE)
    # Invitado del enlace publico (es_invitado=True), correo interno generado.
    invitado_id, email_invitado = crear_paciente(org_id, area_id)

    _crear_evaluacion_en_curso(
        client,
        headers_admin,
        org_id,
        [control_id, invitado_id],
        "Evaluacion Invitados 2026",
    )

    res = client.post("/api/notificaciones/enviar-recordatorios", headers=headers_admin)
    assert res.status_code == 200, res.text
    data = res.json()

    control_det = _detalle_de(data, control_id)
    assert control_det is not None, "El paciente con login pendiente debio evaluarse."
    assert control_det["estadoNotificacion"] == "ENVIADA"

    assert _detalle_de(data, invitado_id) is None, (
        "El invitado del enlace no debe recibir recordatorios."
    )

    destinatarios = [c.args[0] for c in mock_enviar_correo.call_args_list]
    assert email_control in destinatarios
    assert email_invitado not in destinatarios