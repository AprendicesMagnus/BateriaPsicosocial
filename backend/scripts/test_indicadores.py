import httpx

BASE_URL = "http://127.0.0.1:4000/api"

def test_indicadores():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # Login Admin
    res = client.post("/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, f"Error login: {res.text}"
    token_admin = res.json()["token"]
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Consultar indicadores generales
    res = client.get("/indicadores", headers=headers)
    assert res.status_code == 200, f"Error al consultar indicadores: {res.text}"
    data = res.json()

    print("--- RESUMEN DE INDICADORES OBTENIDO ---")
    print(f"  Total Organizaciones: {data['totalOrganizaciones']}")
    print(f"  Total Evaluaciones: {data['totalEvaluaciones']}")
    print(f"  Evaluaciones por Estado: {data['evaluacionesPorEstado']}")
    print(f"  Participación: {data['participacion']}")
    print(f"  Anonimizado: {data['anonimizado']}")

    assert data["totalOrganizaciones"] >= 1
    assert data["totalEvaluaciones"] >= 1
    assert "participacion" in data
    assert "tasaPorcentaje" in data["participacion"]
    print("\n  [OK] Validaciones de indicadores completadas exitosamente")

if __name__ == "__main__":
    test_indicadores()
    print("\n============================================================")
    print("ETAPA D: INDICADORES Y DASHBOARD (RF08) VERIFICADOS OK")
    print("============================================================")
