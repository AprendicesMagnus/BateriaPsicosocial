import uuid

from app.core.nit_utils import calcular_digito_verificador_nit

PASSWORD_PACIENTE = "Paciente1234"


def _login(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def test_paciente_solo_ve_sus_propios_resultados(client, crear_paciente):
    headers_admin = _login(client, "admin@magnussig.com", "Admin1234")

    # Organizacion y area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={
        "nombre": "Empresa Privacidad Pytest SAS",
        "nit": nit_rnd,
        "sector": "Tecnologia",
        "municipio": "Neiva",
        "telefono": "3001234567",
        "email": f"info_{nit_rnd}@test.com",
    })
    assert res.status_code == 200, res.text
    org_id = res.json()["id"]

    res = client.post("/api/organizaciones/areas", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Area Privacidad",
    })
    assert res.status_code == 200, res.text
    area_id = res.json()["id"]

    # Dos pacientes con login en la misma evaluacion
    id_a, email_a = crear_paciente(org_id, area_id=area_id, password=PASSWORD_PACIENTE)
    id_b, email_b = crear_paciente(org_id, area_id=area_id, password=PASSWORD_PACIENTE)

    res = client.get("/api/cuestionarios", headers=headers_admin)
    assert res.status_code == 200, res.text
    version_id = res.json()[0]["id"]

    res = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluacion Privacidad Pytest",
        "versionId": version_id,
        "trabajadoresIds": [str(id_a), str(id_b)],
    })
    assert res.status_code == 200, res.text
    eval_id = res.json()["id"]

    res = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)
    assert res.status_code == 200, res.text
    res = client.post(f"/api/evaluaciones/{eval_id}/notificar", headers=headers_admin)
    assert res.status_code == 200, res.text

    # El paciente A completa su cuestionario; el B no responde nada
    headers_a = _login(client, email_a, PASSWORD_PACIENTE)
    headers_b = _login(client, email_b, PASSWORD_PACIENTE)

    res = client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_a)
    assert res.status_code == 200, res.text

    res = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_a)
    assert res.status_code == 200, res.text
    preguntas = res.json()["preguntas"]
    assert preguntas, "El cuestionario no contiene preguntas."

    for preg in preguntas:
        res = client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_a, json={
            "pregunta_codigo": preg["codigo"],
            "valor": 3,
        })
        assert res.status_code == 200, res.text

    res = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_a)
    assert res.status_code == 200, res.text

    # A consulta: ve solo su resultado y sin el campo trabajadorId
    res = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_a)
    assert res.status_code == 200, res.text
    datos_a = res.json()
    assert len(datos_a) == 1, res.text
    assert "trabajadorId" not in datos_a[0], res.text

    # B consulta: no tiene resultados propios, asi que no debe recibir los de A
    res = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_b)
    assert res.status_code == 400, res.text

    # El admin si ve el resultado de A, identificado
    res = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_admin)
    assert res.status_code == 200, res.text
    datos_admin = res.json()
    assert len(datos_admin) == 1, res.text
    assert datos_admin[0]["trabajadorId"] == str(id_a), res.text