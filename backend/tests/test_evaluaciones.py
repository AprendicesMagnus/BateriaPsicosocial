import uuid
from app.core.nit_utils import calcular_digito_verificador_nit

def test_flujo_completo_evaluacion(client):
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
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
    assert res.status_code == 200
    org_id = res.json()["id"]

    res = client.post("/api/organizaciones/areas", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Sistemas y TI"
    })
    assert res.status_code == 200
    area_id = res.json()["id"]

    # 3. Crear Trabajador
    email_trab = f"trabajador_{uuid.uuid4().hex[:5]}@test.com"
    res = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Ana",
        "apellido": "Gomez",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Desarrolladora Senior"
    })
    assert res.status_code == 200
    trabajador_id = res.json()["id"]

    # 4. Crear Evaluacion
    res = client.get("/api/cuestionarios", headers=headers_admin)
    assert res.status_code == 200
    version_id = res.json()[0]["id"]

    res = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluacion Pytest BRP 2026",
        "versionId": version_id,
        "trabajadoresIds": [trabajador_id]
    })
    assert res.status_code == 200
    eval_id = res.json()["id"]

    # 5. Iniciar y notificar
    res = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)
    assert res.status_code == 200

    res = client.post(f"/api/evaluaciones/{eval_id}/notificar", headers=headers_admin)
    assert res.status_code == 200

    # 6. Login Trabajador y responder
    res = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    assert res.status_code == 200
    token_trab = res.json()["token"]
    headers_trab = {"Authorization": f"Bearer {token_trab}"}

    res = client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)
    assert res.status_code == 200

    res = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_trab)
    assert res.status_code == 200
    preguntas = res.json()["preguntas"]
    assert len(preguntas) == 9

    for preg in preguntas:
        res = client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_trab, json={
            "preguntaId": preg["id"],
            "valor": 3
        })
        assert res.status_code == 200

    res = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_trab)
    assert res.status_code == 200
    resultados = res.json()["resultados"]
    assert len(resultados) == 3

    # 7. Consultar resultados como Admin
    res = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_admin)
    assert res.status_code == 200
    assert len(res.json()) == 1
