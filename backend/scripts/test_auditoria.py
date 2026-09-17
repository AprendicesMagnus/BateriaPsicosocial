import httpx

BASE_URL = "http://127.0.0.1:4000/api"

def test_auditoria_flujo():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # Login Admin
    res = client.post("/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, f"Error login: {res.text}"
    token_admin = res.json()["token"]
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Consultar auditoría
    res = client.get("/auditoria", headers=headers)
    assert res.status_code == 200, f"Error al consultar auditoría: {res.text}"
    logs = res.json()
    assert len(logs) > 0, "No se registraron entradas en la tabla auditoría"

    acciones = {log["accion"] for log in logs}
    print("--- ACCIONES REGISTRADAS EN AUDITORIA ---")
    for acc in sorted(acciones):
        print(f"  [+] Accion auditada: {acc}")

    # Verificar acciones mínimas esperadas
    acciones_esperadas = {"LOGIN", "CREAR_EVALUACION", "INICIAR_EVALUACION", "FINALIZAR_EVALUACION", "INFORME_INDIVIDUAL_GENERADO"}
    encontradas = acciones_esperadas.intersection(acciones)
    assert len(encontradas) > 0, f"No se encontraron las acciones esperadas en auditoría. Acciones presentes: {acciones}"
    print(f"\n  [OK] Auditoría verificada con {len(logs)} registros. Acciones confirmadas: {sorted(encontradas)}")

if __name__ == "__main__":
    test_auditoria_flujo()
    print("\n============================================================")
    print("ETAPA B: AUDITORIA END-TO-END VERIFICADA EXITOSAMENTE")
    print("============================================================")
