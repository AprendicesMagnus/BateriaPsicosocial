import os
import uuid

from app.core.nit_utils import calcular_digito_verificador_nit

PASSWORD_PACIENTE = "Paciente1234"


def test_informe_individual_y_rechazo_anonimato(client, crear_paciente):
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, res.text
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    # 2. Crear org, paciente y evaluacion completada
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers, json={"nombre": "Org Informe Test", "nit": nit_rnd})
    assert res.status_code == 200, res.text
    org_id = res.json()["id"]

    paciente_id, email_pac = crear_paciente(org_id, password=PASSWORD_PACIENTE)

    res = client.get("/api/cuestionarios", headers=headers)
    assert res.status_code == 200, res.text
    version_id = res.json()[0]["id"]

    res = client.post("/api/evaluaciones", headers=headers, json={
        "organizacionId": org_id,
        "nombre": "Eval Informes Test",
        "versionId": version_id,
        "trabajadoresIds": [str(paciente_id)],
    })
    assert res.status_code == 200, res.text
    eval_id = res.json()["id"]

    res = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers)
    assert res.status_code == 200, res.text
    res = client.post(f"/api/evaluaciones/{eval_id}/notificar", headers=headers)
    assert res.status_code == 200, res.text

    # 3. Responder como paciente
    res_l = client.post("/api/auth/login", json={"email": email_pac, "password": PASSWORD_PACIENTE})
    assert res_l.status_code == 200, res_l.text
    headers_p = {"Authorization": f"Bearer {res_l.json()['token']}"}

    res = client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_p)
    assert res.status_code == 200, res.text
    res = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_p)
    assert res.status_code == 200, res.text
    cuest = res.json()

    for preg in cuest["preguntas"]:
        res = client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_p, json={
            "pregunta_codigo": preg["codigo"],
            "valor": 3,
        })
        assert res.status_code == 200, res.text

    res = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_p)
    assert res.status_code == 200, res.text

    # 4. Generar informe individual (Debe ser 200)
    res = client.get(f"/api/evaluaciones/{eval_id}", headers=headers)
    assert res.status_code == 200, res.text
    participante_id = res.json()["detalleParticipantes"][0]["id"]

    res_ind = client.post("/api/informes/individual", headers=headers, json={
        "evaluacionId": eval_id,
        "participanteId": participante_id,
    })
    assert res_ind.status_code == 200, res_ind.text
    data_ind = res_ind.json()
    assert os.path.exists(data_ind["rutaArchivo"])

    # Descargar como Admin (autorizado)
    res_desc = client.get(f"/api/informes/{data_ind['id']}/descargar", headers=headers)
    assert res_desc.status_code == 200, res_desc.text

    # Descargar como paciente dueño (autorizado)
    res_desc_p = client.get(f"/api/informes/{data_ind['id']}/descargar", headers=headers_p)
    assert res_desc_p.status_code == 200, res_desc_p.text

    # 4.5. Intentar descargar como OTRO paciente no autorizado (debe retornar 403)
    _, email_otro = crear_paciente(org_id, password=PASSWORD_PACIENTE)
    res_l_otro = client.post("/api/auth/login", json={"email": email_otro, "password": PASSWORD_PACIENTE})
    assert res_l_otro.status_code == 200, res_l_otro.text
    headers_otro = {"Authorization": f"Bearer {res_l_otro.json()['token']}"}

    res_forbidden = client.get(f"/api/informes/{data_ind['id']}/descargar", headers=headers_otro)
    assert res_forbidden.status_code == 403, res_forbidden.text
    assert "no tiene permisos" in res_forbidden.json()["error"].lower()

    # 5. Generar informe agrupado (Debe ser rechazado con 400 por anonimato al haber < 5 participantes)
    res_agr = client.post("/api/informes/agrupado", headers=headers, json={"evaluacionId": eval_id, "formato": "PDF"})
    assert res_agr.status_code == 400, res_agr.text
    assert "anonimato" in res_agr.json()["error"].lower()