def test_seguimiento_recomendaciones_flow(client):
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Listar seguimientos
    res_list = client.get("/api/seguimiento-recomendaciones", headers=headers)
    assert res_list.status_code == 200
    assert isinstance(res_list.json(), list)

    # 2. Intentar actualizar sin recomendación válida -> 404
    res_post_invalid = client.post(
        "/api/seguimiento-recomendaciones",
        headers=headers,
        json={
            "recomendacionId": "00000000-0000-0000-0000-000000000000",
            "estado": "EN_PROGRESO",
        },
    )
    assert res_post_invalid.status_code in [404, 400]


def test_fecha_limite_seguimiento(client, db_session):
    import uuid
    from datetime import date, timedelta
    from app.models.survey import Recomendacion
    from app.models.organization import Organizacion

    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Crear una organización para la prueba
    org = Organizacion(nombre="Empresa Test Seguimiento", nit=f"900{uuid.uuid4().int % 100000000:08d}-1")
    db_session.add(org)
    db_session.commit()
    org_id = str(org.id)

    # Obtener una recomendación sembrada directamente de la base de datos
    rec = db_session.query(Recomendacion).first()
    assert rec is not None, "No hay recomendaciones sembradas para la prueba"
    rec_id = str(rec.id)

    hoy = date.today()
    fecha_pasada = (hoy - timedelta(days=1)).isoformat()
    fecha_futura = (hoy + timedelta(days=30)).isoformat()

    # 1. Fecha pasada + PENDIENTE => vencida = true
    res = client.post(
        "/api/seguimiento-recomendaciones",
        headers=headers,
        json={"organizacionId": org_id, "recomendacionId": rec_id, "estado": "PENDIENTE", "fechaLimite": fecha_pasada},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["fechaLimite"] == fecha_pasada
    assert data["vencida"] is True

    # 2. Fecha futura => vencida = false
    res = client.post(
        "/api/seguimiento-recomendaciones",
        headers=headers,
        json={"organizacionId": org_id, "recomendacionId": rec_id, "estado": "PENDIENTE", "fechaLimite": fecha_futura},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["vencida"] is False

    # 3. Fecha pasada + IMPLEMENTADA => vencida = false
    res = client.post(
        "/api/seguimiento-recomendaciones",
        headers=headers,
        json={"organizacionId": org_id, "recomendacionId": rec_id, "estado": "IMPLEMENTADA", "fechaLimite": fecha_pasada},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["vencida"] is False

    # 4. POST sin fechaLimite conserva la fecha existente
    res = client.post(
        "/api/seguimiento-recomendaciones",
        headers=headers,
        json={"organizacionId": org_id, "recomendacionId": rec_id, "estado": "PENDIENTE"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["fechaLimite"] == fecha_pasada

    # 5. POST con fechaLimite null la borra
    res = client.post(
        "/api/seguimiento-recomendaciones",
        headers=headers,
        json={"organizacionId": org_id, "recomendacionId": rec_id, "estado": "PENDIENTE", "fechaLimite": None},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["fechaLimite"] is None
