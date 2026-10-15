import uuid

from app.core.nit_utils import calcular_digito_verificador_nit

PASSWORD_PACIENTE = "Paciente1234"


def test_flujo_completo_evaluacion(client, crear_paciente):
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, res.text
    token_admin = res.json()["token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 2. Crear Organizacion y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={
        "nombre": "Empresa Test Pytest SAS",
        "nit": nit_rnd,
        "sector": "Tecnologia",
        "municipio": "Neiva",
        "telefono": "3001234567",
        "email": f"info_{nit_rnd}@test.com"
    })
    assert res.status_code == 200, res.text
    org_id = res.json()["id"]

    res = client.post("/api/organizaciones/areas", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Sistemas y TI"
    })
    assert res.status_code == 200, res.text
    area_id = res.json()["id"]

    # 3. Crear paciente con login (el rol TRABAJADOR ya no existe)
    paciente_id, email_pac = crear_paciente(org_id, area_id=area_id, password=PASSWORD_PACIENTE)

    # 4. Crear Evaluacion
    res = client.get("/api/cuestionarios", headers=headers_admin)
    assert res.status_code == 200, res.text
    version_id = res.json()[0]["id"]

    res = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluacion Pytest BRP 2026",
        "versionId": version_id,
        "trabajadoresIds": [str(paciente_id)]
    })
    assert res.status_code == 200, res.text
    eval_id = res.json()["id"]

    # 5. Iniciar y notificar
    res = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)
    assert res.status_code == 200, res.text

    res = client.post(f"/api/evaluaciones/{eval_id}/notificar", headers=headers_admin)
    assert res.status_code == 200, res.text

    # 6. Login del paciente y responder
    res = client.post("/api/auth/login", json={"email": email_pac, "password": PASSWORD_PACIENTE})
    assert res.status_code == 200, res.text
    token_pac = res.json()["token"]
    headers_pac = {"Authorization": f"Bearer {token_pac}"}

    res = client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_pac)
    assert res.status_code == 200, res.text

    res = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac)
    assert res.status_code == 200, res.text
    preguntas = res.json()["preguntas"]
    assert len(preguntas) == 9

    for preg in preguntas:
        res = client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_pac, json={
            "pregunta_codigo": preg["codigo"],
            "valor": 3
        })
        assert res.status_code == 200, res.text

    res = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_pac)
    assert res.status_code == 200, res.text
    resultados = res.json()["resultados"]
    assert len(resultados) == 3

    # 7. Consultar resultados como Admin
    res = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_admin)
    assert res.status_code == 200, res.text
    assert len(res.json()) == 1