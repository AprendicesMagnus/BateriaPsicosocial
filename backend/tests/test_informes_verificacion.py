import os
import uuid

from app.core.nit_utils import calcular_digito_verificador_nit

PASSWORD_PACIENTE = "Paciente1234"


def test_verificacion_informe_individual(client, crear_paciente):
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, res.text
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    # 2. Crear org, paciente y evaluacion completada
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers, json={"nombre": "Org Verif Test", "nit": nit_rnd})
    assert res.status_code == 200, res.text
    org_id = res.json()["id"]

    paciente_id, email_pac = crear_paciente(org_id, password=PASSWORD_PACIENTE)

    res = client.get("/api/cuestionarios", headers=headers)
    assert res.status_code == 200, res.text
    version_id = res.json()[0]["id"]

    res = client.post("/api/evaluaciones", headers=headers, json={
        "organizacionId": org_id,
        "nombre": "Eval Verif Test",
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

    # 4. Generar informe individual
    res = client.get(f"/api/evaluaciones/{eval_id}", headers=headers)
    assert res.status_code == 200, res.text
    participante_id = res.json()["detalleParticipantes"][0]["id"]

    res_ind = client.post("/api/informes/individual", headers=headers, json={
        "evaluacionId": eval_id,
        "participanteId": participante_id,
    })
    assert res_ind.status_code == 200, res_ind.text
    data = res_ind.json()

    assert "codigoVerificacion" in data, "Falta codigoVerificacion en la respuesta"
    assert data["codigoVerificacion"], "codigoVerificacion está vacío"
    assert "hashSha256" in data, "Falta hashSha256 en la respuesta"
    assert len(data["hashSha256"]) == 64, "hashSha256 no tiene 64 caracteres"

    codigo = data["codigoVerificacion"]

    # 5. Endpoint público de verificación (sin autenticación)
    res_v = client.get(f"/api/informes/verificar/{codigo}")
    assert res_v.status_code == 200, res_v.text
    v = res_v.json()
    assert v["valido"] is True
    assert v["tipo"] == "INDIVIDUAL"
    assert v["hashSha256"] == data["hashSha256"]
    assert "rutaArchivo" not in v
    assert "trabajadorId" not in v
    assert "id" not in v

    # 6. Código inexistente retorna 404
    res_nf = client.get("/api/informes/verificar/codigo-que-no-existe-abc123")
    assert res_nf.status_code == 404, res_nf.text
