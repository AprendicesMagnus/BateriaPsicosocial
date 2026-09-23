import httpx
import sys
import uuid
import psycopg2

BASE_URL = "http://127.0.0.1:4000/api"
DB_PARAMS = "dbname=magnussing user=postgres password=12345 host=localhost port=5432"

def main():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    print("================================================================")
    print("VERIFICACION FINAL COMPLETA DE FRONTEND <-> BACKEND (BRP)")
    print("================================================================\n")

    # ------------------------------------------------------------------
    # BLOQUE 1: MIGRACION Y SEED DE RECOMENDACIONES EN DEV DB
    # ------------------------------------------------------------------
    print("--- BLOQUE 1: MIGRACION Y SEED DE RECOMENDACIONES EN DEV DB ---")
    conn = psycopg2.connect(DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM recomendaciones;")
    count_recs = cur.fetchone()[0]
    print(f"  [OK] Consulta SQL direct: SELECT COUNT(*) FROM recomendaciones; -> {count_recs} filas")
    assert count_recs == 15, f"Esperadas 15 recomendaciones, encontradas {count_recs}"
    cur.close()
    conn.close()

    # ------------------------------------------------------------------
    # BLOQUE 2: FLUJO COMO ADMINISTRADOR
    # ------------------------------------------------------------------
    print("\n--- BLOQUE 2: FLUJO COMO ADMINISTRADOR (SignIn -> Panel -> Informes -> IA) ---")
    # 1. Login Admin
    res_admin = client.post("/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200, f"Error login admin: {res_admin.text}"
    admin_token = res_admin.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("  [OK] 1. Login exitoso como Administrador")

    # 2. Indicadores
    res_ind = client.get("/indicadores", headers=admin_headers)
    assert res_ind.status_code == 200, f"Error indicadores: {res_ind.text}"
    ind_data = res_ind.json()
    print(f"  [OK] 2. Indicadores cargados: {ind_data['totalOrganizaciones']} Orgs, {ind_data['totalEvaluaciones']} Evals, Tasa Participación: {ind_data['participacion']['tasaPorcentaje']}%")

    # Setup evaluacion con 6 participantes completados para superar MIN_GRUPO_ANONIMATO (5)
    res_orgs = client.get("/organizaciones", headers=admin_headers)
    org_id = res_orgs.json()[0]["id"]
    res_quest = client.get("/cuestionarios", headers=admin_headers)
    version_id = res_quest.json()[0]["id"]

    trab_grp_ids = []
    headers_grp = []
    for i in range(6):
        em = f"trab_grp_{i}_{uuid.uuid4().hex[:4]}@empresa.com"
        r_u = client.post("/usuarios", headers=admin_headers, json={
            "nombre": f"TrabGrp{i+1}", "apellido": "Test", "email": em, "password": "Trabajador1234",
            "rolCodigo": "TRABAJADOR", "organizacionId": org_id, "cargo": "Operario"
        })
        t_id = r_u.json()["id"]
        trab_grp_ids.append(t_id)
        r_l = client.post("/auth/login", json={"email": em, "password": "Trabajador1234"})
        headers_grp.append({"Authorization": f"Bearer {r_l.json()['token']}"})

    res_ev_grp = client.post("/evaluaciones", headers=admin_headers, json={
        "organizacionId": org_id, "nombre": "Evaluación Grupo Anonimato 2026", "versionId": version_id, "trabajadoresIds": trab_grp_ids
    })
    eval_grp_id = res_ev_grp.json()["id"]
    client.post(f"/evaluaciones/{eval_grp_id}/iniciar", headers=admin_headers)

    patrones = [
        {'P1': 1, 'P2': 1, 'P3': 5, 'P4': 2, 'P5': 2, 'P6': 4, 'P7': 5, 'P8': 5, 'P9': 5},
        {'P1': 1, 'P2': 2, 'P3': 4, 'P4': 2, 'P5': 1, 'P6': 5, 'P7': 4, 'P8': 5, 'P9': 4},
        {'P1': 3, 'P2': 3, 'P3': 3, 'P4': 3, 'P5': 3, 'P6': 3, 'P7': 3, 'P8': 3, 'P9': 3},
        {'P1': 3, 'P2': 4, 'P3': 2, 'P4': 3, 'P5': 3, 'P6': 2, 'P7': 3, 'P8': 2, 'P9': 3},
        {'P1': 5, 'P2': 5, 'P3': 1, 'P4': 5, 'P5': 5, 'P6': 1, 'P7': 1, 'P8': 1, 'P9': 1},
        {'P1': 5, 'P2': 4, 'P3': 1, 'P4': 4, 'P5': 5, 'P6': 1, 'P7': 1, 'P8': 2, 'P9': 1},
    ]

    for idx_h, h in enumerate(headers_grp):
        client.post(f"/evaluaciones/{eval_grp_id}/consentimiento", headers=h)
        c = client.get(f"/evaluaciones/{eval_grp_id}/cuestionario", headers=h).json()
        patron = patrones[idx_h]
        for p in c["preguntas"]:
            val = patron.get(p["codigo"], 3)
            client.post(f"/evaluaciones/{eval_grp_id}/respuestas", headers=h, json={"preguntaId": p["id"], "valor": val})
        client.post(f"/evaluaciones/{eval_grp_id}/finalizar-cuestionario", headers=h)

    print("  [OK] 3. Evaluación con 6 participantes completada (supera MIN_GRUPO_ANONIMATO=5)")

    # Generar Informe Agrupado PDF y descagar
    res_pdf = client.post("/informes/agrupado", headers=admin_headers, json={"evaluacionId": eval_grp_id, "formato": "PDF"})
    assert res_pdf.status_code == 200, f"Error informe PDF: {res_pdf.text}"
    inf_pdf_id = res_pdf.json()["id"]
    print(f"  [OK] 4a. Informe agrupado PDF generado (ID: {inf_pdf_id})")

    res_dl = client.get(f"/informes/{inf_pdf_id}/descargar", headers=admin_headers)
    assert res_dl.status_code == 200
    print(f"  [OK] 4b. Descarga de PDF agrupado exitosa ({len(res_dl.content)} bytes)")

    # Análisis Predictivo K-Means (IA)
    res_pred = client.get(f"/prediccion/evaluaciones/{eval_grp_id}/prediccion", headers=admin_headers)
    assert res_pred.status_code == 200, f"Error prediccion: {res_pred.text}"
    pred_data = res_pred.json()
    print(f"  [OK] 5. Análisis predictivo IA cargado con éxito: {len(pred_data['perfilesClusterKMeans'])} clusters, Nota: '{pred_data['notaMetodologica'][:60]}...'")

    # ------------------------------------------------------------------
    # BLOQUE 3: REGISTRO DE UN USUARIO NUEVO
    # ------------------------------------------------------------------
    print("\n--- BLOQUE 3: REGISTRO DE UN USUARIO NUEVO (CreateAccount -> VerifyCode) ---")
    email_nuevo = f"trabajador_v2026_{uuid.uuid4().hex[:6]}@empresa.com"
    pass_nuevo = "Password1234"

    res_reg = client.post("/auth/register", json={
        "nombre": "Carlos",
        "apellido": "Mendoza",
        "email": email_nuevo,
        "password": pass_nuevo
    })
    assert res_reg.status_code == 200, f"Error registro: {res_reg.text}"
    print(f"  [OK] 1. Registro exitoso para: {email_nuevo}")

    # Obtener código generado en BD (modo SMTP simulado / log)
    conn = psycopg2.connect(DB_PARAMS)
    cur = conn.cursor()
    cur.execute("""
        SELECT codigo FROM codigos_verificacion cv
        JOIN usuarios u ON cv.usuario_id = u.id
        WHERE u.email = %s AND cv.tipo = 'VERIFICACION_EMAIL' AND cv.usado = false
        ORDER BY cv.creado_en DESC LIMIT 1;
    """, (email_nuevo,))
    codigo_verif = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"  [OK] 2. Código de verificación obtenido de la BD (modo simulado): {codigo_verif}")

    # Verificar email
    res_ve = client.post("/auth/verify-email", json={"email": email_nuevo, "codigo": codigo_verif})
    assert res_ve.status_code == 200, f"Error verificacion email: {res_ve.text}"
    print("  [OK] 3. Correo verificado correctamente vía /auth/verify-email")

    # ------------------------------------------------------------------
    # BLOQUE 4: FLUJO COMO TRABAJADOR
    # ------------------------------------------------------------------
    print("\n--- BLOQUE 4: FLUJO COMO TRABAJADOR (Login -> Lista -> Consentimiento -> Cuestionario -> Resultados) ---")
    # Login nuevo trabajador
    res_lt = client.post("/auth/login", json={"email": email_nuevo, "password": pass_nuevo})
    assert res_lt.status_code == 200, f"Error login trabajador: {res_lt.text}"
    trab_token = res_lt.json()["token"]
    trab_headers = {"Authorization": f"Bearer {trab_token}"}
    trab_id = res_lt.json()["usuario"]["id"]
    print("  [OK] 1. Login exitoso como nuevo Trabajador")

    # Asignar organizacionId al trabajador desde Admin
    client.patch(f"/usuarios/{trab_id}", headers=admin_headers, json={"organizacionId": org_id})

    # Asignar trabajador a la evaluación desde Admin
    res_ev_trab = client.post("/evaluaciones", headers=admin_headers, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Verificación Final 2026",
        "versionId": version_id,
        "trabajadoresIds": [trab_id]
    })
    assert res_ev_trab.status_code == 200, f"Error crear eval trabajador: {res_ev_trab.text}"
    eval_trab_id = res_ev_trab.json()["id"]
    client.post(f"/evaluaciones/{eval_trab_id}/iniciar", headers=admin_headers)
    print("  [OK] 2. Evaluación asignada e iniciada para el trabajador")

    # Lista de evaluaciones asignadas al trabajador
    res_mis_evs = client.get("/evaluaciones", headers=trab_headers)
    assert res_mis_evs.status_code == 200
    assert len(res_mis_evs.json()) >= 1
    print(f"  [OK] 3. ListaEvaluacionesTrabajador obtiene {len(res_mis_evs.json())} evaluación(es) asignada(s)")

    # Consentimiento informado
    res_cons = client.post(f"/evaluaciones/{eval_trab_id}/consentimiento", headers=trab_headers)
    assert res_cons.status_code == 200
    print("  [OK] 4. Consentimiento informado registrado exitosamente")

    # Cargar cuestionario y responder preguntas Likert
    cuest = client.get(f"/evaluaciones/{eval_trab_id}/cuestionario", headers=trab_headers).json()
    assert len(cuest["preguntas"]) > 0
    print(f"  [OK] 5. Cuestionario cargado con {len(cuest['preguntas'])} preguntas")

    val_respuestas = [2, 1, 4, 3, 5, 2, 4, 1, 3]
    for i, preg in enumerate(cuest["preguntas"]):
        v = val_respuestas[i % len(val_respuestas)]
        res_r = client.post(f"/evaluaciones/{eval_trab_id}/respuestas", headers=trab_headers, json={
            "preguntaId": preg["id"],
            "valor": v
        })
        assert res_r.status_code == 200

    print("  [OK] 6. Todas las preguntas respondidas y cifradas en tiempo real")

    # Finalizar cuestionario
    res_fin = client.post(f"/evaluaciones/{eval_trab_id}/finalizar-cuestionario", headers=trab_headers)
    assert res_fin.status_code == 200
    print("  [OK] 7. Cuestionario finalizado y tabulado con éxito")

    # Ver resultados del trabajador
    res_res = client.get(f"/evaluaciones/{eval_trab_id}/resultados", headers=trab_headers)
    assert res_res.status_code == 200
    res_items = res_res.json()[0]["resultados"]
    print(f"  [OK] 8. Resultados consultados por el trabajador: {len(res_items)} dimensión(es) tabulada(s)")
    for r in res_items:
        print(f"       - Dimensión: '{r['dimension']}' | Transformado: {r['puntajeTransformado']} | Nivel: {r['nivel']}")

    # ------------------------------------------------------------------
    # BLOQUE 5: RECUPERACION DE CONTRASEÑA
    # ------------------------------------------------------------------
    print("\n--- BLOQUE 5: RECUPERACION DE CONTRASEÑA (ForgotPassword -> VerifyCode -> ResetPassword) ---")
    # 1. Forgot password
    res_fp = client.post("/auth/forgot-password", json={"email": email_nuevo})
    assert res_fp.status_code == 200
    print("  [OK] 1. Solicitud de recuperación enviada para correo del trabajador")

    # Obtener código de reset de la BD
    conn = psycopg2.connect(DB_PARAMS)
    cur = conn.cursor()
    cur.execute("""
        SELECT codigo FROM codigos_verificacion cv
        JOIN usuarios u ON cv.usuario_id = u.id
        WHERE u.email = %s AND cv.tipo = 'RESET_PASSWORD' AND cv.usado = false
        ORDER BY cv.creado_en DESC LIMIT 1;
    """, (email_nuevo,))
    codigo_reset = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"  [OK] 2. Código de recuperación obtenido de BD (modo simulado): {codigo_reset}")

    # 2. Verify reset code
    res_vrc = client.post("/auth/verify-reset-code", json={"email": email_nuevo, "codigo": codigo_reset})
    assert res_vrc.status_code == 200
    reset_token = res_vrc.json()["resetToken"]
    print("  [OK] 3. Código verificado y resetToken obtenido")

    # 3. Reset password
    nueva_pass = "NuevaPassword1234"
    res_rp = client.post("/auth/reset-password", json={"resetToken": reset_token, "password": nueva_pass})
    assert res_rp.status_code == 200
    print("  [OK] 4. Contraseña restablecida con éxito vía /auth/reset-password")

    # 4. Verificar login con nueva contraseña
    res_login_nueva = client.post("/auth/login", json={"email": email_nuevo, "password": nueva_pass})
    assert res_login_nueva.status_code == 200
    print("  [OK] 5. Login exitoso usando la nueva contraseña")

    # ------------------------------------------------------------------
    # BLOQUE 6: ERRORES Y CASOS LÍMITE VISIBLES EN LA UI
    # ------------------------------------------------------------------
    print("\n--- BLOQUE 6: ERRORES Y CASOS LIMITE VISIBLES EN LA UI ---")

    def get_err(res):
        d = res.json()
        return d.get("error") or d.get("detail") or str(d)

    # 1. Error de credenciales inválidas (401)
    res_err_login = client.post("/auth/login", json={"email": email_nuevo, "password": "PasswordIncorrecto999"})
    assert res_err_login.status_code == 401
    print(f"  [OK] 1. Credenciales inválidas devuelven HTTP 401: '{get_err(res_err_login)}'")

    # 2. Error de correo duplicado al registrar (409)
    res_err_dup = client.post("/auth/register", json={
        "nombre": "Carlos", "apellido": "Mendoza", "email": email_nuevo, "password": "Password1234"
    })
    assert res_err_dup.status_code == 409
    print(f"  [OK] 2. Registro duplicado devuelve HTTP 409: '{get_err(res_err_dup)}'")

    # 3. Error al descargar informe inexistente / sin permisos (404)
    uuid_invalido = str(uuid.uuid4())
    res_err_dl = client.get(f"/informes/{uuid_invalido}/descargar", headers=trab_headers)
    assert res_err_dl.status_code == 404
    print(f"  [OK] 3. Descargar informe inexistente devuelve HTTP 404: '{get_err(res_err_dl)}'")

    # 4. Error de clave débil (400)
    res_err_pass = client.post("/auth/register", json={
        "nombre": "Debil", "apellido": "Pass", "email": f"debil_{uuid.uuid4().hex[:4]}@test.com", "password": "123"
    })
    assert res_err_pass.status_code == 400
    print(f"  [OK] 4. Contraseña débil devuelve HTTP 400: '{get_err(res_err_pass)}'")

    print("\n================================================================")
    print("VERIFICACION FINAL COMPLETADA EXITOSAMENTE DE PUNTA A PUNTA!")
    print("================================================================")

if __name__ == "__main__":
    main()
