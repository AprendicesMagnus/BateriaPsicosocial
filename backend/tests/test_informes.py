import os
import uuid
from app.core.nit_utils import calcular_digito_verificador_nit

def test_informe_individual_y_rechazo_anonimato(client):
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    token_admin = res.json()["token"]
    headers = {"Authorization": f"Bearer {token_admin}"}

    # 2. Crear org, area, trabajador y evaluacion completada
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post("/api/organizaciones", headers=headers, json={"nombre": "Org Informe Test", "nit": nit_rnd})
    org_id = res.json()["id"]

    email_trab = f"trab_{uuid.uuid4().hex[:5]}@test.com"
    res = client.post("/api/usuarios", headers=headers, json={
        "nombre": "Pedro", "apellido": "Infante", "email": email_trab, "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR", "organizacionId": org_id
    })
    trab_id = res.json()["id"]

    res = client.get("/api/cuestionarios", headers=headers)
    version_id = res.json()[0]["id"]

    res = client.post("/api/evaluaciones", headers=headers, json={"organizacionId": org_id, "nombre": "Eval Informes Test", "versionId": version_id, "trabajadoresIds": [trab_id]})
    eval_id = res.json()["id"]

    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers)
    client.post(f"/api/evaluaciones/{eval_id}/notificar", headers=headers)

    # 3. Responder como trabajador
    res_l = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    token_t = res_l.json()["token"]
    headers_t = {"Authorization": f"Bearer {token_t}"}

    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_t)
    cuest = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_t).json()

    for preg in cuest["preguntas"]:
        client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_t, json={"preguntaId": preg["id"], "valor": 3})

    client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_t)

    # 4. Generar informe individual (Debe ser 200)
    res_ind = client.post("/api/informes/individual", headers=headers, json={"evaluacionId": eval_id, "participanteId": (client.get(f"/api/evaluaciones/{eval_id}", headers=headers).json()["detalleParticipantes"][0]["id"])})
    assert res_ind.status_code == 200
    data_ind = res_ind.json()
    assert os.path.exists(data_ind["rutaArchivo"])

    # Descargar como Admin (autorizado)
    res_desc = client.get(f"/api/informes/{data_ind['id']}/descargar", headers=headers)
    assert res_desc.status_code == 200

    # Descargar como Trabajador dueño (autorizado)
    res_desc_t = client.get(f"/api/informes/{data_ind['id']}/descargar", headers=headers_t)
    assert res_desc_t.status_code == 200

    # 4.5. Intentar descargar como OTRO trabajador no autorizado (debe retornar 403)
    email_otro = f"otro_{uuid.uuid4().hex[:5]}@test.com"
    client.post("/api/usuarios", headers=headers, json={
        "nombre": "Otro", "apellido": "Trabajador", "email": email_otro, "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR", "organizacionId": org_id
    })
    res_l_otro = client.post("/api/auth/login", json={"email": email_otro, "password": "Trabajador1234"})
    token_otro = res_l_otro.json()["token"]
    headers_otro = {"Authorization": f"Bearer {token_otro}"}

    res_forbidden = client.get(f"/api/informes/{data_ind['id']}/descargar", headers=headers_otro)
    assert res_forbidden.status_code == 403
    assert "no tiene permisos" in res_forbidden.json()["error"].lower()

    # 5. Generar informe agrupado (Debe ser rechazado con 400 por anonimato al haber < 5 participantes)
    res_agr = client.post("/api/informes/agrupado", headers=headers, json={"evaluacionId": eval_id, "formato": "PDF"})
    assert res_agr.status_code == 400
    assert "anonimato" in res_agr.json()["error"].lower()
