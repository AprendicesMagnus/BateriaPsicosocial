import uuid

from app.core.nit_utils import calcular_digito_verificador_nit

PASSWORD_PACIENTE = "Paciente1234"


def test_analisis_predictivo_kmeans(client, crear_paciente):
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, res.text
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    # 2. Crear Organizacion y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={
        "nombre": "Empresa Predictivo K-Means SAS",
        "nit": nit_rnd,
        "sector": "Servicios",
        "municipio": "Neiva",
    })
    assert res.status_code == 200, res.text
    org_id = res.json()["id"]

    res = client.post("/api/organizaciones/areas", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Operaciones y Calidad",
    })
    assert res.status_code == 200, res.text
    area_id = res.json()["id"]

    # 3. Crear 6 pacientes con login para superar MIN_GRUPO_ANONIMATO=5
    res = client.get("/api/cuestionarios", headers=headers_admin)
    assert res.status_code == 200, res.text
    version_id = res.json()[0]["id"]

    pacientes_ids = []
    emails = []
    for _ in range(6):
        paciente_id, email = crear_paciente(org_id, area_id=area_id, password=PASSWORD_PACIENTE)
        pacientes_ids.append(str(paciente_id))
        emails.append(email)

    # 4. Crear e iniciar Evaluacion
    res = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Predictiva 2026",
        "versionId": version_id,
        "trabajadoresIds": pacientes_ids,
    })
    assert res.status_code == 200, res.text
    eval_id = res.json()["id"]

    res = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)
    assert res.status_code == 200, res.text

    # 5. Responder cuestionarios con respuestas variadas por perfil
    # Perfil A (1-2): Alto riesgo en Liderazgo y Demandas
    # Perfil B (3-4): Riesgo medio balanceado
    # Perfil C (5-6): Bajo riesgo / saludable
    patrones_respuestas = [
        {'P1': 1, 'P2': 1, 'P3': 5, 'P4': 2, 'P5': 2, 'P6': 4, 'P7': 5, 'P8': 5, 'P9': 5},
        {'P1': 1, 'P2': 2, 'P3': 4, 'P4': 2, 'P5': 1, 'P6': 5, 'P7': 4, 'P8': 5, 'P9': 4},
        {'P1': 3, 'P2': 3, 'P3': 3, 'P4': 3, 'P5': 3, 'P6': 3, 'P7': 3, 'P8': 3, 'P9': 3},
        {'P1': 3, 'P2': 4, 'P3': 2, 'P4': 3, 'P5': 3, 'P6': 2, 'P7': 3, 'P8': 2, 'P9': 3},
        {'P1': 5, 'P2': 5, 'P3': 1, 'P4': 5, 'P5': 5, 'P6': 1, 'P7': 1, 'P8': 1, 'P9': 1},
        {'P1': 5, 'P2': 4, 'P3': 1, 'P4': 4, 'P5': 5, 'P6': 1, 'P7': 1, 'P8': 2, 'P9': 1},
    ]

    for i, email in enumerate(emails):
        res_l = client.post("/api/auth/login", json={"email": email, "password": PASSWORD_PACIENTE})
        assert res_l.status_code == 200, res_l.text
        h_pac = {"Authorization": f"Bearer {res_l.json()['token']}"}

        res = client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=h_pac)
        assert res.status_code == 200, res.text

        res = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=h_pac)
        assert res.status_code == 200, res.text
        cuest = res.json()

        patron = patrones_respuestas[i]
        for preg in cuest["preguntas"]:
            val = patron.get(preg["codigo"], 3)
            res = client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=h_pac, json={
                "pregunta_codigo": preg["codigo"],
                "valor": val,
            })
            assert res.status_code == 200, res.text

        res = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=h_pac)
        assert res.status_code == 200, res.text

    # 6. Consultar análisis predictivo como Admin
    res_pred = client.get(f"/api/prediccion/evaluaciones/{eval_id}/prediccion", headers=headers_admin)
    assert res_pred.status_code == 200, f"Error al consultar predicción: {res_pred.text}"
    data_pred = res_pred.json()

    assert data_pred["totalParticipantesAnalizados"] == 6
    assert len(data_pred["perfilesClusterKMeans"]) == 3
    assert len(data_pred["incidenciaRiesgoPorDimension"]) == 3
    assert "notaMetodologica" in data_pred
    assert "estrategiaEntrenamiento" in data_pred