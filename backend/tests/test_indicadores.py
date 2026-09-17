def test_consulta_indicadores(client):
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res_login.json()["token"]

    res = client.get("/api/indicadores", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "totalOrganizaciones" in data
    assert "totalEvaluaciones" in data
    assert "participacion" in data
