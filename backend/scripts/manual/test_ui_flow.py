import os
import httpx
import uuid

BASE_URL = "http://127.0.0.1:4000/api"

def test_ui_flow():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    print("--- 1. LOGIN DE ADMINISTRADOR ---")
    res = client.post("/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, f"Error en login: {res.text}"
    token = res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  [OK] Admin autenticado con éxito")

    print("\n--- 2. VER INDICADORES Y METRICAS EN PANEL ---")
    res = client.get("/indicadores", headers=headers)
    assert res.status_code == 200, f"Error al consultar indicadores: {res.text}"
    ind_data = res.json()
    assert ind_data["totalOrganizaciones"] >= 1
    assert ind_data["totalEvaluaciones"] >= 1
    print(f"  [OK] Indicadores obtenidos: {ind_data['totalOrganizaciones']} Org(s), {ind_data['totalEvaluaciones']} Eval(s), Tasa Participación: {ind_data['participacion']['tasaPorcentaje']}%")

    print("\n--- 3. CREAR Y COMPLETAR EVALUACION PARA GENERAR INFORME ---")
    res_orgs = client.get("/organizaciones", headers=headers)
    org_id = res_orgs.json()[0]["id"]
    res_quest = client.get("/cuestionarios", headers=headers)
    version_id = res_quest.json()[0]["id"]

    email_trab = f"trab_ui_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/usuarios", headers=headers, json={
        "nombre": "Elena", "apellido": "Vargas", "email": email_trab, "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR", "organizacionId": org_id, "cargo": "Analista UI"
    })
    trab_id = res_trab.json()["id"]

    res_eval = client.post("/evaluaciones", headers=headers, json={
        "organizacionId": org_id, "nombre": "Evaluación Flujo UI 2026", "versionId": version_id, "trabajadoresIds": [trab_id]
    })
    eval_id = res_eval.json()["id"]

    client.post(f"/evaluaciones/{eval_id}/iniciar", headers=headers)

    # Login trabajador
    res_lt = client.post("/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    token_t = res_lt.json()["token"]
    headers_t = {"Authorization": f"Bearer {token_t}"}

    client.post(f"/evaluaciones/{eval_id}/consentimiento", headers=headers_t)
    cuest = client.get(f"/evaluaciones/{eval_id}/cuestionario", headers=headers_t).json()

    # Worker gives high risk answers on Leadership & Demands
    respuestas = {'P1': 1, 'P2': 1, 'P3': 5, 'P4': 3, 'P5': 3, 'P6': 3, 'P7': 5, 'P8': 5, 'P9': 5}
    for preg in cuest["preguntas"]:
        v = respuestas.get(preg["codigo"], 3)
        client.post(f"/evaluaciones/{eval_id}/respuestas", headers=headers_t, json={"preguntaId": preg["id"], "valor": v})

    client.post(f"/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_t)
    print("  [OK] Evaluación completada por el trabajador")

    print("\n--- 4. GENERAR Y DESCARGAR INFORME INDIVIDUAL CON RECOMENDACIONES ---")
    participante_id = client.get(f"/evaluaciones/{eval_id}", headers=headers).json()["detalleParticipantes"][0]["id"]
    res_inf = client.post("/informes/individual", headers=headers, json={"evaluacionId": eval_id, "participanteId": participante_id})
    assert res_inf.status_code == 200, f"Error generar informe: {res_inf.text}"
    informe_id = res_inf.json()["id"]
    print(f"  [OK] Informe individual generado: ID {informe_id}")

    res_dl = client.get(f"/informes/{informe_id}/descargar", headers=headers)
    assert res_dl.status_code == 200
    assert len(res_dl.content) > 1000
    print(f"  [OK] Archivo PDF descargado correctamente ({len(res_dl.content)} bytes)")

    print("\n============================================================")
    print("PRUEBA PRIORIDAD 3: FLUJO COMPLETO DESDE LA UI EXITOSO")
    print("============================================================")

if __name__ == "__main__":
    test_ui_flow()
