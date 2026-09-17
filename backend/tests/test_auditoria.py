def test_consulta_auditoria(client):
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res_login.json()["token"]

    res = client.get("/api/auditoria", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
