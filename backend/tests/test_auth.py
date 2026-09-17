def test_login_exitoso_admin(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["usuario"]["email"] == "admin@magnussig.com"
    assert data["usuario"]["rol"] == "ADMINISTRADOR"

def test_login_credenciales_invalidas(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "WrongPassword123"})
    assert res.status_code == 401
    assert "error" in res.json()

def test_me_autenticado(client):
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token = res_login.json()["token"]
    
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["usuario"]["email"] == "admin@magnussig.com"
