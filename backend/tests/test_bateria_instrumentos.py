"""
Pruebas para la integración de los 5 instrumentos de la Batería Psicosocial (Etapa 2.6).
- Verificación del sembrado de las 5 versiones y conteo de preguntas.
- Asignación automática de Intralaboral Forma A (Jefatura/Profesional) vs Forma B (Auxiliar/Operario) al guardar la Ficha.
- Exclusión mutua: un participante nunca puede quedar con ambas formas asignadas simultáneamente.
"""
import uuid
import pytest
from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.intralaboral_oficial import cargar_referencia
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.survey import CuestionarioVersion, Pregunta


@pytest.fixture(autouse=True)
def setup_seed_instrumentos(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_seed_crea_cinco_versiones_con_preguntas_correctas(db_session):
    esperados = {
        "FICHA_DATOS": 21,
        "ESTRES": 31,
        "EXTRALABORAL": 31,
        "INTRALABORAL_A": 123,
        "INTRALABORAL_B": 97,
    }

    for codigo, num_preguntas in esperados.items():
        version = (
            db_session.query(CuestionarioVersion)
            .filter(CuestionarioVersion.codigo == codigo, CuestionarioVersion.vigente.is_(True))
            .first()
        )
        assert version is not None, f"No se encontró la versión {codigo} en la base de datos."
        total_preguntas = sum(len(dim.preguntas) for dim in version.dimensiones)
        assert total_preguntas == num_preguntas, (
            f"La versión {codigo} debió tener {num_preguntas} preguntas, pero tiene {total_preguntas}."
        )

    # Verificar escala específica de Estrés (1-4)
    v_estres = db_session.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == "ESTRES").first()
    for dim in v_estres.dimensiones:
        for p in dim.preguntas:
            assert p.valor_minimo == 1
            assert p.valor_maximo == 4


def test_guardar_ficha_jefatura_asigna_intralaboral_a(client):
    # 1. Login admin y preparar entorno
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa FormaA SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Gerencia"})
    area_id = res_area.json()["id"]

    email_trab = f"jefe_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Carlos",
        "apellido": "Jefe",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Director General"
    })
    trabajador_id = res_trab.json()["id"]

    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluacion BRP 2026",
        "trabajadoresIds": [trabajador_id]
    })
    eval_id = res_eval.json()["id"]

    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    # 2. Login trabajador y consentimiento
    res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

    # 3. Guardar Ficha con tipoCargo de Jefatura
    res_ficha = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json={
        "nombreCompleto": "Carlos Jefe",
        "sexo": "Masculino",
        "anioNacimiento": "1985",
        "estadoCivil": "Casado (a)",
        "nivelEstudios": "Postgrado / Maestría",
        "ocupacion": "Administrador",
        "residenciaCiudad": "Bogotá",
        "residenciaDepartamento": "Cundinamarca",
        "estrato": "4",
        "tipoVivienda": "Propia",
        "personasACargo": 2,
        "trabajoCiudad": "Bogotá",
        "trabajoDepartamento": "Cundinamarca",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "5",
        "nombreCargo": "Director General",
        "tipoCargo": "Jefatura - tiene personal a cargo",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "3",
        "areaODepartamento": "Gerencia",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    })
    assert res_ficha.status_code == 200
    assert res_ficha.json()["intralaboralAsignado"] == "INTRALABORAL_A"

    # 4. Verificar lista de instrumentos
    res_inst = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_trab)
    assert res_inst.status_code == 200
    codigos_asignados = [item["codigo"] for item in res_inst.json()]
    assert "INTRALABORAL_A" in codigos_asignados
    assert "INTRALABORAL_B" not in codigos_asignados


def test_guardar_ficha_auxiliar_asigna_intralaboral_b(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa FormaB SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Operaciones"})
    area_id = res_area.json()["id"]

    email_trab = f"auxiliar_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Ana",
        "apellido": "Auxiliar",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Auxiliar de Archivo"
    })
    trabajador_id = res_trab.json()["id"]

    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluacion BRP 2026 B",
        "trabajadoresIds": [trabajador_id]
    })
    eval_id = res_eval.json()["id"]

    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

    res_ficha = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json={
        "nombreCompleto": "Ana Auxiliar",
        "sexo": "Femenino",
        "anioNacimiento": "1992",
        "estadoCivil": "Soltero (a)",
        "nivelEstudios": "Técnico / Tecnólogo",
        "ocupacion": "Auxiliar",
        "residenciaCiudad": "Medellín",
        "residenciaDepartamento": "Antioquia",
        "estrato": "3",
        "tipoVivienda": "Arrendada",
        "personasACargo": 1,
        "trabajoCiudad": "Medellín",
        "trabajoDepartamento": "Antioquia",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "2",
        "nombreCargo": "Auxiliar de Archivo",
        "tipoCargo": "Auxiliar, asistente administrativo, asistente técnico",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "2",
        "areaODepartamento": "Operaciones",
        "tipoContrato": "Término Fijo",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    })
    assert res_ficha.status_code == 200
    assert res_ficha.json()["intralaboralAsignado"] == "INTRALABORAL_B"

    res_inst = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_trab)
    assert res_inst.status_code == 200
    codigos_asignados = [item["codigo"] for item in res_inst.json()]
    assert "INTRALABORAL_B" in codigos_asignados
    assert "INTRALABORAL_A" not in codigos_asignados


def test_participante_no_puede_tener_ambas_formas_intralaboral(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa CambioCargo SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Planta"})
    area_id = res_area.json()["id"]

    email_trab = f"cambio_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Pedro",
        "apellido": "Cambio",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Operario"
    })
    trabajador_id = res_trab.json()["id"]

    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluacion Cambio Cargo",
        "trabajadoresIds": [trabajador_id]
    })
    eval_id = res_eval.json()["id"]

    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

    # 1. Primero guarda como Jefatura (Forma A)
    ficha_data = {
        "nombreCompleto": "Pedro Cambio",
        "sexo": "Masculino",
        "anioNacimiento": "1990",
        "estadoCivil": "Soltero (a)",
        "nivelEstudios": "Profesional",
        "ocupacion": "Ingeniero",
        "residenciaCiudad": "Cali",
        "residenciaDepartamento": "Valle",
        "estrato": "3",
        "tipoVivienda": "Propia",
        "personasACargo": 0,
        "trabajoCiudad": "Cali",
        "trabajoDepartamento": "Valle",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "1",
        "nombreCargo": "Supervisor",
        "tipoCargo": "Jefatura - tiene personal a cargo",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "1",
        "areaODepartamento": "Planta",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    }
    client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json=ficha_data)

    res_inst1 = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_trab)
    codigos1 = [item["codigo"] for item in res_inst1.json()]
    assert "INTRALABORAL_A" in codigos1
    assert "INTRALABORAL_B" not in codigos1

    # 2. Ahora actualiza la Ficha a Operario (Forma B)
    ficha_data["tipoCargo"] = "Operario, operador, ayudante, servicios generales"
    res_ficha2 = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json=ficha_data)
    assert res_ficha2.json()["intralaboralAsignado"] == "INTRALABORAL_B"

    res_inst2 = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_trab)
    codigos2 = [item["codigo"] for item in res_inst2.json()]
    assert "INTRALABORAL_B" in codigos2
    assert "INTRALABORAL_A" not in codigos2, "No debe conservar la Forma A si la Ficha cambió a un cargo de Forma B."


def test_get_cuestionario_resuelve_instrumento_real_pendiente(client):
    """
    Verifica que GET /cuestionario (usado por el Panel) resuelva el instrumento real pendiente
    vía participante_instrumentos (p.ej. ESTRES de 31 preguntas) en lugar de devolver
    el cuestionario de demostración BRP_FORMA_A (de 9 preguntas).
    """
    # 1. Login admin y crear evaluación
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa PanelSync SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Operaciones"})
    area_id = res_area.json()["id"]

    email_trab = f"operario_panel_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Pedro",
        "apellido": "Operario",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Operario de Producción"
    })
    trabajador_id = res_trab.json()["id"]

    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Panel Real 2026",
        "trabajadoresIds": [trabajador_id]
    })
    eval_id = res_eval.json()["id"]

    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    # 2. Login trabajador y consentimiento
    res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

    # 3. Guardar Ficha de Datos Generales (completa FICHA_DATOS y asigna INTRALABORAL_B)
    res_ficha = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json={
        "nombreCompleto": "Pedro Operario",
        "sexo": "Masculino",
        "anioNacimiento": "1995",
        "estadoCivil": "Soltero (a)",
        "nivelEstudios": "Secundaria / Bachillerato",
        "ocupacion": "Operario",
        "residenciaCiudad": "Bucaramanga",
        "residenciaDepartamento": "Santander",
        "estrato": "2",
        "tipoVivienda": "Propia",
        "personasACargo": 1,
        "trabajoCiudad": "Bucaramanga",
        "trabajoDepartamento": "Santander",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "3",
        "nombreCargo": "Operario de Producción",
        "tipoCargo": "Operario, operador, ayudante, servicios generales",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "3",
        "areaODepartamento": "Operaciones",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    })
    assert res_ficha.status_code == 200
    assert res_ficha.json()["intralaboralAsignado"] == "INTRALABORAL_B"

    # 4. Simular Panel llamando GET /cuestionario: DEBE responder ESTRES (31 preguntas), NO BRP_FORMA_A (9 preguntas)
    res_quest = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_trab)
    assert res_quest.status_code == 200
    data_quest = res_quest.json()

    assert data_quest["codigo"] == "ESTRES"
    assert data_quest["nombre"] == "Cuestionario para la Evaluación del Estrés"
    preguntas = data_quest["preguntas"]
    assert len(preguntas) == 31, f"Se esperaban 31 preguntas de Estrés, pero llegaron {len(preguntas)}"
    assert preguntas[0]["codigo"] == "EST_1"
    assert preguntas[0]["enunciado"] == "Dolores en el cuello y espalda o tensión muscular."

    # 5. Responder las 31 preguntas de ESTRES y finalizar el instrumento
    for preg in preguntas:
        res_r = client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_trab, json={
            "preguntaId": preg["id"],
            "valor": 3
        })
        assert res_r.status_code == 200

    res_fin = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_trab)
    assert res_fin.status_code == 200
    assert res_fin.json()["completadoTotal"] is False

    # 6. Siguiente llamada a GET /cuestionario desde el Panel: DEBE responder EXTRALABORAL (31 preguntas)
    res_quest2 = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_trab)
    assert res_quest2.status_code == 200
    data_quest2 = res_quest2.json()

    assert data_quest2["codigo"] == "EXTRALABORAL"
    assert len(data_quest2["preguntas"]) == 31
    assert data_quest2["preguntas"][0]["codigo"] == "EXT_1"


def test_crear_evaluacion_sin_version_id_inicializa_los_5_instrumentos_reales(client):
    """
    Verifica que la creación por defecto de una evaluación (POST /api/evaluaciones sin versionId en el body)
    inicialice automáticamente los instrumentos reales (FICHA_DATOS, ESTRES, EXTRALABORAL)
    y asigne la Forma Intralaboral B al guardar la Ficha, garantizando que el Panel
    resuelva Estrés (31 preguntas, EST_1) y no BRP_FORMA_A.
    """
    # 1. Login admin
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

    # 2. Crear Org, Area y Trabajador
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa Default Flow SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Mantenimiento"})
    area_id = res_area.json()["id"]

    email_trab = f"operario_defecto_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Jorge",
        "apellido": "Operario",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Técnico Mantenimiento"
    })
    trabajador_id = res_trab.json()["id"]

    # 3. Crear evaluación SIN versionId en el body (camino por defecto de Evaluador SST)
    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación Flujo Por Defecto 2026",
        "trabajadoresIds": [trabajador_id]
        # NOTA: Sin versionId explícito
    })
    assert res_eval.status_code == 200
    eval_id = res_eval.json()["id"]

    # Iniciar evaluación
    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    # 4. Login trabajador y consentimiento
    res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

    # 5. Verificar instrumentos inicializados antes de guardar Ficha (deben ser FICHA_DATOS, ESTRES, EXTRALABORAL)
    res_inst_iniciales = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_trab)
    assert res_inst_iniciales.status_code == 200
    insts_iniciales = res_inst_iniciales.json()

    assert len(insts_iniciales) == 3
    assert insts_iniciales[0]["codigo"] == "FICHA_DATOS" and insts_iniciales[0]["orden"] == 1
    assert insts_iniciales[1]["codigo"] == "ESTRES" and insts_iniciales[1]["orden"] == 2
    assert insts_iniciales[2]["codigo"] == "EXTRALABORAL" and insts_iniciales[2]["orden"] == 3

    # 6. Guardar Ficha con tipoCargo Operario -> debe asignar INTRALABORAL_B como orden 4
    res_ficha = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json={
        "nombreCompleto": "Jorge Operario",
        "sexo": "Masculino",
        "anioNacimiento": "1991",
        "estadoCivil": "Casado (a)",
        "nivelEstudios": "Técnico / Tecnólogo",
        "ocupacion": "Técnico",
        "residenciaCiudad": "Manizales",
        "residenciaDepartamento": "Caldas",
        "estrato": "3",
        "tipoVivienda": "Propia",
        "personasACargo": 2,
        "trabajoCiudad": "Manizales",
        "trabajoDepartamento": "Caldas",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "4",
        "nombreCargo": "Técnico Mantenimiento",
        "tipoCargo": "Operario, operador, ayudante, servicios generales",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "4",
        "areaODepartamento": "Mantenimiento",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    })
    assert res_ficha.status_code == 200
    assert res_ficha.json()["intralaboralAsignado"] == "INTRALABORAL_B"

    # Verificar que INTRALABORAL_B quedó registrado con orden 4
    res_inst_post_ficha = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_trab)
    assert res_inst_post_ficha.status_code == 200
    insts_post_ficha = res_inst_post_ficha.json()
    assert len(insts_post_ficha) == 4
    inst_intra = next(i for i in insts_post_ficha if i["codigo"] == "INTRALABORAL_B")
    assert inst_intra["orden"] == 4

    # 7. Simular consulta del Panel (GET /cuestionario): DEBE resolver ESTRES (31 preguntas, EST_1), NO BRP_FORMA_A
    res_panel = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_trab)
    assert res_panel.status_code == 200
    data_panel = res_panel.json()

    assert data_panel["codigo"] == "ESTRES"
    assert data_panel["nombre"] == "Cuestionario para la Evaluación del Estrés"
    assert len(data_panel["preguntas"]) == 31
    assert data_panel["preguntas"][0]["codigo"] == "EST_1"
    assert data_panel["preguntas"][0]["enunciado"] == "Dolores en el cuello y espalda o tensión muscular."


def test_flujo_completo_evaluacion_real_tabula_todas_las_dimensiones(client):
    """
    Prueba E2E real (Etapa 5):
    - Crea una evaluación sin versionId (camino real por defecto).
    - Completa Ficha Datos, Estrés (31), Extralaboral (31) e Intralaboral B (97) mediante la API real.
    - Verifica que se tabulen las 3 dimensiones de los cuestionarios reales y que cada una reciba un nivel de riesgo válido.
    """
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Org y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa E2E Tabulacion SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Logística"})
    area_id = res_area.json()["id"]

    # 3. Crear Trabajador
    email_trab = f"auxiliar_e2e_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Pedro",
        "apellido": "Auxiliar",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Auxiliar de Bodega"
    })
    trab_id = res_trab.json()["id"]

    # 4. Crear Evaluación sin versionId (flujo real)
    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación E2E BRP Real 2026",
        "trabajadoresIds": [trab_id]
    })
    assert res_eval.status_code == 200
    eval_id = res_eval.json()["id"]

    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    # 5. Login Trabajador y consentimiento
    res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

    # 6. Guardar Ficha (asigna INTRALABORAL_B)
    res_ficha = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json={
        "nombreCompleto": "Pedro Auxiliar",
        "sexo": "Masculino",
        "anioNacimiento": "1990",
        "estadoCivil": "Soltero (a)",
        "nivelEstudios": "Bachillerato",
        "ocupacion": "Auxiliar",
        "residenciaCiudad": "Bogotá",
        "residenciaDepartamento": "Cundinamarca",
        "estrato": "3",
        "tipoVivienda": "Arrendada",
        "personasACargo": 1,
        "trabajoCiudad": "Bogotá",
        "trabajoDepartamento": "Cundinamarca",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "2",
        "nombreCargo": "Auxiliar Bodega",
        "tipoCargo": "Auxiliar, asistente administrativo, asistente técnico",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "2",
        "areaODepartamento": "Logística",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    })
    assert res_ficha.status_code == 200
    assert res_ficha.json()["intralaboralAsignado"] == "INTRALABORAL_B"

    # 7. Responder y finalizar secuencialmente los 3 instrumentos reales: ESTRES, EXTRALABORAL, INTRALABORAL_B
    instrumentos_completados = 0
    final_res = None
    for _ in range(3):
        q_data = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_trab).json()
        if q_data.get("estado") == "COMPLETADA":
            break
        for p in q_data["preguntas"]:
            client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_trab, json={"preguntaId": p["id"], "valor": 3})
        res_fin = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_trab)
        assert res_fin.status_code == 200
        final_res = res_fin.json()
        instrumentos_completados += 1

    assert instrumentos_completados == 3
    assert final_res["completadoTotal"] is True

    # 8. Consultar resultados tabulados como Admin y verificar cada ResultadoDimension
    res_resultados = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_admin)
    assert res_resultados.status_code == 200
    datos_resultados = res_resultados.json()
    assert len(datos_resultados) == 1
    detalles_participante = datos_resultados[0]
    resultados = detalles_participante["resultados"]

    # Deben haberse generado: 1 Ficha + 1 Estrés + 1 Extralaboral + la estructura real
    # de Intralaboral B (16 dimensiones + 4 dominios + 1 total del cuestionario = 21),
    # tomada de la misma referencia oficial (Tablas 21-34) que usa el sembrado real,
    # no un número fijo que se rompería si el manual cambia de estructura.
    ref_b = cargar_referencia()["forma_B"]
    n_intralaboral_b = len(ref_b["dimensiones"]) + len(ref_b["dominios"]) + 1  # +1 = total del cuestionario
    n_esperados = 1 + 1 + 1 + n_intralaboral_b  # Ficha + Estrés + Extralaboral + Intralaboral B
    assert len(resultados) == n_esperados, f"Se esperaban {n_esperados} ResultadoDimension pero se generaron {len(resultados)}"

    psicometricos = [r for r in resultados if r["dominio"] != "Ficha de Datos Generales"]
    assert len(psicometricos) == n_esperados - 1

    niveles_validos = {"SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"}
    for r in psicometricos:
        assert r["dimension"] is not None and r["dimension"] != ""
        assert r["nivel"] in niveles_validos, f"La dimensión {r['dimension']} tiene un nivel no clasificado: {r['nivel']}"
        assert 0.0 <= r["puntajeTransformado"] <= 100.0


def test_flujo_completo_evaluacion_real_tabula_todas_las_dimensiones_forma_a(client):
    """
    Misma prueba E2E que test_flujo_completo_evaluacion_real_tabula_todas_las_dimensiones,
    pero con un participante Jefatura/Profesional (Intralaboral Forma A) en vez de Auxiliar
    (Forma B). Cubre la otra mitad de la estructura real: 19 dimensiones + 4 dominios + 1
    total de Forma A, que la prueba de Forma B no ejercita.
    """
    # 1. Login Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res_admin.status_code == 200
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Org y Area
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res_org = client.post("/api/organizaciones", headers=headers_admin, json={"nombre": "Empresa E2E Tabulacion Forma A SAS", "nit": nit_rnd})
    org_id = res_org.json()["id"]

    res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={"organizacionId": org_id, "nombre": "Gerencia"})
    area_id = res_area.json()["id"]

    # 3. Crear Trabajador (Jefatura)
    email_trab = f"jefe_e2e_{uuid.uuid4().hex[:5]}@test.com"
    res_trab = client.post("/api/usuarios", headers=headers_admin, json={
        "nombre": "Carlos",
        "apellido": "Jefe",
        "email": email_trab,
        "password": "Trabajador1234",
        "rolCodigo": "TRABAJADOR",
        "organizacionId": org_id,
        "areaId": area_id,
        "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
        "cargo": "Director General"
    })
    trab_id = res_trab.json()["id"]

    # 4. Crear Evaluación sin versionId (flujo real)
    res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": "Evaluación E2E BRP Real Forma A 2026",
        "trabajadoresIds": [trab_id]
    })
    assert res_eval.status_code == 200
    eval_id = res_eval.json()["id"]

    client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

    # 5. Login Trabajador y consentimiento
    res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
    headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
    client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

    # 6. Guardar Ficha con tipoCargo de Jefatura (asigna INTRALABORAL_A)
    res_ficha = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_trab, json={
        "nombreCompleto": "Carlos Jefe",
        "sexo": "Masculino",
        "anioNacimiento": "1985",
        "estadoCivil": "Casado (a)",
        "nivelEstudios": "Postgrado / Maestría",
        "ocupacion": "Administrador",
        "residenciaCiudad": "Bogotá",
        "residenciaDepartamento": "Cundinamarca",
        "estrato": "4",
        "tipoVivienda": "Propia",
        "personasACargo": 2,
        "trabajoCiudad": "Bogotá",
        "trabajoDepartamento": "Cundinamarca",
        "antiguedadEmpresaMenosUnAnio": False,
        "antiguedadEmpresa": "5",
        "nombreCargo": "Director General",
        "tipoCargo": "Jefatura - tiene personal a cargo",
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "3",
        "areaODepartamento": "Gerencia",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
    })
    assert res_ficha.status_code == 200
    assert res_ficha.json()["intralaboralAsignado"] == "INTRALABORAL_A"

    # 7. Responder y finalizar secuencialmente los 3 instrumentos reales: ESTRES, EXTRALABORAL, INTRALABORAL_A
    instrumentos_completados = 0
    final_res = None
    for _ in range(3):
        q_data = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_trab).json()
        if q_data.get("estado") == "COMPLETADA":
            break
        for p in q_data["preguntas"]:
            client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_trab, json={"preguntaId": p["id"], "valor": 3})
        res_fin = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_trab)
        assert res_fin.status_code == 200
        final_res = res_fin.json()
        instrumentos_completados += 1

    assert instrumentos_completados == 3
    assert final_res["completadoTotal"] is True

    # 8. Consultar resultados tabulados como Admin y verificar cada ResultadoDimension
    res_resultados = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_admin)
    assert res_resultados.status_code == 200
    datos_resultados = res_resultados.json()
    assert len(datos_resultados) == 1
    detalles_participante = datos_resultados[0]
    resultados = detalles_participante["resultados"]

    # 1 Ficha + 1 Estrés + 1 Extralaboral + estructura real de Intralaboral A
    # (19 dimensiones + 4 dominios + 1 total = 24), calculado contra la misma
    # referencia oficial que usa el sembrado real.
    ref_a = cargar_referencia()["forma_A"]
    n_intralaboral_a = len(ref_a["dimensiones"]) + len(ref_a["dominios"]) + 1  # +1 = total del cuestionario
    n_esperados = 1 + 1 + 1 + n_intralaboral_a  # Ficha + Estrés + Extralaboral + Intralaboral A
    assert len(resultados) == n_esperados, f"Se esperaban {n_esperados} ResultadoDimension pero se generaron {len(resultados)}"

    psicometricos = [r for r in resultados if r["dominio"] != "Ficha de Datos Generales"]
    assert len(psicometricos) == n_esperados - 1

    niveles_validos = {"SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"}
    for r in psicometricos:
        assert r["dimension"] is not None and r["dimension"] != ""
        assert r["nivel"] in niveles_validos, f"La dimensión {r['dimension']} tiene un nivel no clasificado: {r['nivel']}"
        assert 0.0 <= r["puntajeTransformado"] <= 100.0