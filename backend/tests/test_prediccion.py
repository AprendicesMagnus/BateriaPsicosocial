import uuid

def test_analisis_predictivo_kmeans(client):
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    token_admin = res.json()["token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 2. Crear Organizacion y Area
    nit_rnd = f"9{str(uuid.uuid4().int)[:8]}"
    res = client.post("/api/organizaciones", headers=headers_admin, json={
        "nombre": "Empresa Predictivo K-Means SAS",
        "nit": nit_rnd,
        "sector": "Servicios",
        "municipio": "Neiva"
    })
    assert res.status_code == 200
    org_id = res.json()["id"]

    res = client.post("/api/organizaciones/areas", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Operaciones y Calidad"
    })
    assert res.status_code == 200
    area_id = res.json()["id"]

    # 3. Crear 6 trabajadores para superar MIN_GRUPO_ANONIMATO=5
    trabajadores_ids = []
    headers_trabajadores = []

    res = client.get("/api/cuestionarios", headers=headers_admin)
    version_id = res.json()[0]["id"]

    for i in range(6):
        email_trab = f"trab_pred_{i}_{uuid.uuid4().hex[:4]}@test.com"
        res = client.post("/api/usuarios", headers=headers_admin, json={
            "nombre": f"Trabajador{i+1}",
            "apellido": "Test",
            "email": email_trab,
            "password": "Trabajador1234",
            "rolCodigo": "TRABAJADOR",
            "organizacionId": org_id,
            "areaId": area_id,
            "numeroIdentificacion": f"CC{uuid.uuid4().hex[:8]}",
            "cargo": "Operario"
        })
        assert res.status_code == 200
        t_id = res.json()["id"]
        trabajadores_ids.append(t_id)

        # Login trabajador
        res_l = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
        headers_trabajadores.append({"Authorization": f"Bearer {res_l.json()['token']}"})

    # 4. Crear e iniciar Evaluacion
    res = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Predictiva 2026",
        "versionId": version_id,
        "trabajadoresIds": trabajadores_ids
    })
    assert res.status_code == 200
    eval_id = res.json()["id"]

    res = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)
    assert res.status_code == 200

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

    for i, h_trab in enumerate(headers_trabajadores):
        client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=h_trab)
        cuest = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=h_trab).json()

        patron = patrones_respuestas[i]
        for preg in cuest["preguntas"]:
            val = patron.get(preg["codigo"], 3)
            client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=h_trab, json={
                "preguntaId": preg["id"],
                "valor": val
            })
        client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=h_trab)

    # 6. Consultar análisis predictivo como Admin
    res_pred = client.get(f"/api/prediccion/evaluaciones/{eval_id}/prediccion", headers=headers_admin)
    assert res_pred.status_code == 200, f"Error al consultar predicción: {res_pred.text}"
    data_pred = res_pred.json()

    assert data_pred["totalParticipantesAnalizados"] == 6
    assert len(data_pred["perfilesClusterKMeans"]) == 3
    assert len(data_pred["incidenciaRiesgoPorDimension"]) == 3
    assert "notaMetodologica" in data_pred
    assert "estrategiaEntrenamiento" in data_pred
