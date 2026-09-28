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
