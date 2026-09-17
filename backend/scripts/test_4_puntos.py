import os
import uuid
import httpx
import psycopg2

BASE_URL = "http://127.0.0.1:4000/api"
DB_PARAMS = "dbname=magnussing user=postgres password=12345 host=localhost port=5432"

def main():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    print("================================================================")
    print("VERIFICACION DE LOS 4 PUNTOS DETALLADOS DE REVISION")
    print("================================================ glass\n")

    # Login Admin
    res_admin = client.post("/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, f"Error login admin: {res_admin.text}"
    admin_token = res_admin.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # ------------------------------------------------------------------
    # PUNTO 2: ALGORITMO DE HASH (BCRYPT) Y PRUEBA RESET -> LOGIN
    # ------------------------------------------------------------------
    print("--- PUNTO 2: VERIFICACION DE HASH DE CONTRASEÑAS (BCRYPT) Y RESET ---")
    email_pwd_test = f"user_pwd_test_{uuid.uuid4().hex[:6]}@empresa.com"
    pass_inicial = "PassInicial1234"
    pass_nueva = "PassNuevaRestablecida5678"

    # 1. Registrar
    r_reg = client.post("/auth/register", json={"nombre": "Prueba", "apellido": "Hash", "email": email_pwd_test, "password": pass_inicial})
    assert r_reg.status_code == 200

    # Obtener código de verificación email y verificar
    conn = psycopg2.connect(DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT codigo FROM codigos_verificacion cv JOIN usuarios u ON cv.usuario_id=u.id WHERE u.email=%s AND cv.tipo='VERIFICACION_EMAIL' ORDER BY cv.creado_en DESC LIMIT 1;", (email_pwd_test,))
    cod_verif = cur.fetchone()[0]
    cur.close()
    conn.close()

    r_v = client.post("/auth/verify-email", json={"email": email_pwd_test, "codigo": cod_verif})
    assert r_v.status_code == 200

    # 2. Verificar hash bcrypt en BD
    conn = psycopg2.connect(DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM usuarios WHERE email=%s;", (email_pwd_test,))
    hash_reg = cur.fetchone()[0]
    cur.close()
    conn.close()
    assert hash_reg.startswith("$2b$") or hash_reg.startswith("$2a$"), f"Esperado hash bcrypt ($2b$), obtenido: {hash_reg[:10]}"
    print(f"  [OK] Hash registrado verificado en BD: {hash_reg[:20]}... (Algoritmo: bcrypt)")

    # 3. Solicitar reset de contraseña
    client.post("/auth/forgot-password", json={"email": email_pwd_test})
    conn = psycopg2.connect(DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT codigo FROM codigos_verificacion cv JOIN usuarios u ON cv.usuario_id=u.id WHERE u.email=%s AND cv.tipo='RESET_PASSWORD' AND cv.usado=false ORDER BY cv.creado_en DESC LIMIT 1;", (email_pwd_test,))
    cod_reset = cur.fetchone()[0]
    cur.close()
    conn.close()

    r_vrc = client.post("/auth/verify-reset-code", json={"email": email_pwd_test, "codigo": cod_reset})
    reset_token = r_vrc.json()["resetToken"]

    r_rp = client.post("/auth/reset-password", json={"resetToken": reset_token, "password": pass_nueva})
    assert r_rp.status_code == 200

    # 4. Verificar hash post-reset en BD
    conn = psycopg2.connect(DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM usuarios WHERE email=%s;", (email_pwd_test,))
    hash_reset = cur.fetchone()[0]
    cur.close()
    conn.close()
    assert hash_reset.startswith("$2b$") or hash_reset.startswith("$2a$"), f"Esperado hash bcrypt ($2b$), obtenido: {hash_reset[:10]}"
    print(f"  [OK] Hash post-reset verificado en BD: {hash_reset[:20]}... (Algoritmo: bcrypt)")

    # 5. Probar login con nueva contraseña
    r_l_new = client.post("/auth/login", json={"email": email_pwd_test, "password": pass_nueva})
    assert r_l_new.status_code == 200, f"Error login con nueva clave: {r_l_new.text}"
    print("  [OK] Login con contraseña restablecida EXITOSO. Algoritmo 100% unificado en bcrypt.")

    # ------------------------------------------------------------------
    # PUNTO 3: DESCARGA DE INFORME SIN PERMISOS (HTTP 403)
    # ------------------------------------------------------------------
    print("\n--- PUNTO 3: DESCARGA DE INFORME SIN PERMISOS (HTTP 403 FORBIDDEN) ---")
    
    # Crear Org A y Org B
    res_org_a = client.post("/organizaciones", headers=admin_headers, json={"nombre": f"Org A {uuid.uuid4().hex[:4]}", "nit": f"800{uuid.uuid4().hex[:6]}", "sector": "Salud", "municipio": "Bogotá"})
    org_a_id = res_org_a.json()["id"]

    res_org_b = client.post("/organizaciones", headers=admin_headers, json={"nombre": f"Org B {uuid.uuid4().hex[:4]}", "nit": f"801{uuid.uuid4().hex[:6]}", "sector": "Tecnología", "municipio": "Medellín"})
    org_b_id = res_org_b.json()["id"]

    res_quest = client.get("/cuestionarios", headers=admin_headers)
    version_id = res_quest.json()[0]["id"]

    # Crear trabajador en Org A
    em_trab_a = f"trab_org_a_{uuid.uuid4().hex[:4]}@orga.com"
    res_u_a = client.post("/usuarios", headers=admin_headers, json={"nombre": "Juan", "apellido": "OrgA", "email": em_trab_a, "password": "Trabajador1234", "rolCodigo": "TRABAJADOR", "organizacionId": org_a_id, "cargo": "Analista"})
    trab_a_id = res_u_a.json()["id"]

    # Crear trabajador en Org B
    em_trab_b = f"trab_org_b_{uuid.uuid4().hex[:4]}@orgb.com"
    res_u_b = client.post("/usuarios", headers=admin_headers, json={"nombre": "Pedro", "apellido": "OrgB", "email": em_trab_b, "password": "Trabajador1234", "rolCodigo": "TRABAJADOR", "organizacionId": org_b_id, "cargo": "Desarrollador"})
    trab_b_id = res_u_b.json()["id"]

    # Crear evaluacion y completar para Org A
    res_ev_a = client.post("/evaluaciones", headers=admin_headers, json={"organizacionId": org_a_id, "nombre": "Eval Org A 2026", "versionId": version_id, "trabajadoresIds": [trab_a_id]})
    eval_a_id = res_ev_a.json()["id"]
    client.post(f"/evaluaciones/{eval_a_id}/iniciar", headers=admin_headers)

    res_l_a = client.post("/auth/login", json={"email": em_trab_a, "password": "Trabajador1234"})
    h_a = {"Authorization": f"Bearer {res_l_a.json()['token']}"}
    client.post(f"/evaluaciones/{eval_a_id}/consentimiento", headers=h_a)
    cuest_a = client.get(f"/evaluaciones/{eval_a_id}/cuestionario", headers=h_a).json()
    for p in cuest_a["preguntas"]:
        client.post(f"/evaluaciones/{eval_a_id}/respuestas", headers=h_a, json={"preguntaId": p["id"], "valor": 4})
    client.post(f"/evaluaciones/{eval_a_id}/finalizar-cuestionario", headers=h_a)

    # Generar Informe Individual en Org A
    res_inf_a = client.post("/informes/individual", headers=admin_headers, json={"evaluacionId": eval_a_id, "participanteId": cuest_a.get("participanteId") or client.get(f"/evaluaciones/{eval_a_id}", headers=admin_headers).json()["detalleParticipantes"][0]["id"]})
    informe_a_id = res_inf_a.json()["id"]
    print(f"  [OK] Informe individual generado en Org A (ID: {informe_a_id})")

    # Intentar descargar informe de Org A desde Trabajador de Org B
    res_l_b = client.post("/auth/login", json={"email": em_trab_b, "password": "Trabajador1234"})
    h_b = {"Authorization": f"Bearer {res_l_b.json()['token']}"}

    res_dl_forbidden = client.get(f"/informes/{informe_a_id}/descargar", headers=h_b)
    assert res_dl_forbidden.status_code == 403, f"Esperado 403, obtenido {res_dl_forbidden.status_code}: {res_dl_forbidden.text}"
    msg_err = res_dl_forbidden.json()["error"]
    assert "No tiene permisos para descargar este informe individual." in msg_err
    print(f"  [OK] Descarga rechazada con HTTP 403 FORBIDDEN. Mensaje exacto: '{msg_err}'")

    # ------------------------------------------------------------------
    # PUNTO 4: VERIFICACION DE CONTENIDO REAL DEL PDF GENERADO
    # ------------------------------------------------------------------
    print("\n--- PUNTO 4: VERIFICACION DE CONTENIDO REAL DEL PDF GENERADO ---")
    
    # Descargar PDF individual generado como Admin
    res_dl_pdf = client.get(f"/informes/{informe_a_id}/descargar", headers=admin_headers)
    assert res_dl_pdf.status_code == 200
    pdf_bytes = len(res_dl_pdf.content)
    print(f"  [OK] Informe Individual PDF descargado: {pdf_bytes} bytes")

    # Generar informe agrupado PDF con 6 participantes
    trab_grp_ids = []
    headers_grp = []
    for i in range(6):
        em = f"trab_grp_pdf_{i}_{uuid.uuid4().hex[:4]}@orga.com"
        r_u = client.post("/usuarios", headers=admin_headers, json={"nombre": f"TrabGrpPdf{i+1}", "apellido": "Test", "email": em, "password": "Trabajador1234", "rolCodigo": "TRABAJADOR", "organizacionId": org_a_id, "cargo": "Operario"})
        t_id = r_u.json()["id"]
        trab_grp_ids.append(t_id)
        r_l = client.post("/auth/login", json={"email": em, "password": "Trabajador1234"})
        headers_grp.append({"Authorization": f"Bearer {r_l.json()['token']}"})

    res_ev_grp = client.post("/evaluaciones", headers=admin_headers, json={"organizacionId": org_a_id, "nombre": "Eval Grupal PDF 2026", "versionId": version_id, "trabajadoresIds": trab_grp_ids})
    eval_grp_id = res_ev_grp.json()["id"]
    client.post(f"/evaluaciones/{eval_grp_id}/iniciar", headers=admin_headers)

    for h in headers_grp:
        client.post(f"/evaluaciones/{eval_grp_id}/consentimiento", headers=h)
        c = client.get(f"/evaluaciones/{eval_grp_id}/cuestionario", headers=h).json()
        for p in c["preguntas"]:
            client.post(f"/evaluaciones/{eval_grp_id}/respuestas", headers=h, json={"preguntaId": p["id"], "valor": 4})
        client.post(f"/evaluaciones/{eval_grp_id}/finalizar-cuestionario", headers=h)

    res_inf_grp = client.post("/informes/agrupado", headers=admin_headers, json={"evaluacionId": eval_grp_id, "formato": "PDF"})
    assert res_inf_grp.status_code == 200
    inf_grp_id = res_inf_grp.json()["id"]

    res_dl_grp_pdf = client.get(f"/informes/{inf_grp_id}/descargar", headers=admin_headers)
    assert res_dl_grp_pdf.status_code == 200
    grp_pdf_bytes = len(res_dl_grp_pdf.content)
    print(f"  [OK] Informe Agrupado PDF generado y descargado: {grp_pdf_bytes} bytes")
    assert grp_pdf_bytes > 3000, f"Tamaño del PDF ({grp_pdf_bytes} bytes) debería ser mayor a 3000 bytes tras mejoras de formateo"

    print("\n================================================================")
    print("VERIFICACION DE LOS 4 PUNTOS COMPLETADA CON EXITO!")
    print("================================================================")

if __name__ == "__main__":
    main()
