import os
import httpx
import uuid

BASE_URL = "http://127.0.0.1:4000/api"

def test_informes_flujo():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Login Admin
    res = client.post("/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, f"Error login: {res.text}"
    token_admin = res.json()["token"]
    headers = {"Authorization": f"Bearer {token_admin}"}

    # 2. Obtener evaluaciones completadas
    res = client.get("/evaluaciones", headers=headers)
    assert res.status_code == 200
    evaluaciones = res.json()
    assert len(evaluaciones) > 0, "Se requiere al menos una evaluación"
    eval_id = evaluaciones[0]["id"]

    # Obtener detalle de evaluación para obtener participanteId
    res = client.get(f"/evaluaciones/{eval_id}", headers=headers)
    assert res.status_code == 200
    detalle = res.json()
    participantes = detalle.get("detalleParticipantes", [])
    assert len(participantes) > 0, "Se requiere al menos un participante"
    participante_id = participantes[0]["id"]

    print("--- TEST INFORMES: Generando Informe Individual ---")
    res = client.post("/informes/individual", headers=headers, json={
        "evaluacionId": eval_id,
        "participanteId": participante_id,
    })
    assert res.status_code == 200, f"Error al generar informe individual: {res.text}"
    info_ind = res.json()
    assert info_ind["tipo"] == "INDIVIDUAL"
    assert info_ind["formato"] == "PDF"
    assert os.path.exists(info_ind["rutaArchivo"]), "El archivo PDF no se creó en disco"
    print(f"  [OK] Informe individual generado: {info_ind['rutaArchivo']}")

    # Descargar informe
    res = client.get(f"/informes/{info_ind['id']}/descargar", headers=headers)
    assert res.status_code == 200
    assert len(res.content) > 0
    print("  [OK] Descarga de informe individual verificada")

    print("--- TEST INFORMES: Probando Control de Anonimato en Informe Agrupado ---")
    res = client.post("/informes/agrupado", headers=headers, json={
        "evaluacionId": eval_id,
        "formato": "PDF",
    })
    # Debe ser rechazado porque hay solo 1 participante completado (min_grupo_anonimato = 5)
    assert res.status_code == 400, f"Se esperaba rechazo 400 por anonimato, pero se obtuvo {res.status_code}: {res.text}"
    err_detail = res.json().get("error", "")
    assert "anonimato" in err_detail.lower(), f"El mensaje de error debió mencionar anonimato: {err_detail}"
    print(f"  [OK] Informe agrupado rechazado correctamente por anonimato: '{err_detail}'")

if __name__ == "__main__":
    test_informes_flujo()
    print("\n============================================================")
    print("ETAPA A: GENERACION Y RECHAZO DE INFORMES VERIFICADA OK")
    print("============================================================")
