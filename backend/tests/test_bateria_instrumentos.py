"""
Pruebas para la integración de los 5 instrumentos de la Batería Psicosocial (Etapa 2.6).
- Verificación del sembrado de las 5 versiones y conteo de preguntas.
- Asignación automática de Intralaboral Forma A (Jefatura/Profesional) vs Forma B (Auxiliar/Operario) al guardar la Ficha.
- Exclusión mutua: un participante nunca puede quedar con ambas formas asignadas simultáneamente.

Los participantes son PACIENTES con login (el rol TRABAJADOR ya no existe), creados con el
fixture crear_paciente.
"""
import uuid

import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.intralaboral_oficial import cargar_referencia
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.survey import CuestionarioVersion

PASSWORD_PACIENTE = "Paciente1234"

TIPO_CARGO_JEFATURA = "Jefatura - tiene personal a cargo"
TIPO_CARGO_AUXILIAR = "Auxiliar, asistente administrativo, asistente técnico"
TIPO_CARGO_OPERARIO = "Operario, operador, ayudante, servicios generales"


@pytest.fixture(autouse=True)
def setup_seed_instrumentos(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


# ─── helpers ───────────────────────────────────────────────────────────────

def _login(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _crear_org_y_area(client, headers_admin, nombre_org, nombre_area):
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    res = client.post(
        "/api/organizaciones",
        headers=headers_admin,
        json={"nombre": nombre_org, "nit": nit_rnd},
    )
    assert res.status_code == 200, res.text
    org_id = res.json()["id"]

    res = client.post(
        "/api/organizaciones/areas",
        headers=headers_admin,
        json={"organizacionId": org_id, "nombre": nombre_area},
    )
    assert res.status_code == 200, res.text
    return org_id, res.json()["id"]


def _preparar_evaluacion(client, crear_paciente, nombre_org, nombre_area, nombre_eval):
    """
    Crea organización, área, un paciente con login y una evaluación SIN versionId
    (camino real por defecto), la inicia y deja el consentimiento aceptado.
    Devuelve (headers_admin, headers_paciente, eval_id).
    """
    headers_admin = _login(client, "admin@magnussig.com", "Admin1234")
    org_id, area_id = _crear_org_y_area(client, headers_admin, nombre_org, nombre_area)
    paciente_id, email = crear_paciente(org_id, area_id=area_id, password=PASSWORD_PACIENTE)

    res = client.post("/api/evaluaciones", headers=headers_admin, json={
        "organizacionId": org_id,
        "nombre": nombre_eval,
        "trabajadoresIds": [str(paciente_id)],
    })
    assert res.status_code == 200, res.text
    eval_id = res.json()["id"]

    res = client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)
    assert res.status_code == 200, res.text

    headers_pac = _login(client, email, PASSWORD_PACIENTE)
    res = client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_pac)
    assert res.status_code == 200, res.text

    return headers_admin, headers_pac, eval_id


def _guardar_ficha(client, headers_pac, eval_id, **cambios):
    datos = {
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
        "tipoCargo": TIPO_CARGO_JEFATURA,
        "antiguedadCargoMenosUnAnio": False,
        "antiguedadCargo": "3",
        "areaODepartamento": "Gerencia",
        "tipoContrato": "Indefinido",
        "horasDiarias": 8,
        "tipoSalario": "Fijo",
        "tienePersonalACargo": True,
    }
    datos.update(cambios)
    res = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_pac, json=datos)
    assert res.status_code == 200, res.text
    return res.json()


def _codigos_instrumentos(client, headers_pac, eval_id):
    res = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_pac)
    assert res.status_code == 200, res.text
    return [item["codigo"] for item in res.json()]


def _responder_y_finalizar(client, headers_pac, eval_id, preguntas):
    for p in preguntas:
        res = client.post(f"/api/evaluaciones/{eval_id}/respuestas", headers=headers_pac, json={
            "pregunta_codigo": p["codigo"],
            "valor": 3,
        })
        assert res.status_code == 200, res.text

    res = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_pac)
    assert res.status_code == 200, res.text
    return res.json()


def _completar_instrumentos(client, headers_pac, eval_id):
    """Responde y finaliza secuencialmente ESTRES, EXTRALABORAL e INTRALABORAL (A o B)."""
    completados = 0
    final_res = None
    for _ in range(3):
        res = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac)
        assert res.status_code == 200, res.text
        q_data = res.json()
        if q_data.get("estado") == "COMPLETADA":
            break
        final_res = _responder_y_finalizar(client, headers_pac, eval_id, q_data["preguntas"])
        completados += 1
    return completados, final_res


def _verificar_resultados_tabulados(client, headers_admin, eval_id, n_intralaboral):
    res = client.get(f"/api/evaluaciones/{eval_id}/resultados", headers=headers_admin)
    assert res.status_code == 200, res.text
    datos_resultados = res.json()
    assert len(datos_resultados) == 1, res.text
    resultados = datos_resultados[0]["resultados"]

    # 1 Ficha + 1 Estrés + 1 Extralaboral + estructura real del Intralaboral
    n_esperados = 1 + 1 + 1 + n_intralaboral
    assert len(resultados) == n_esperados, (
        f"Se esperaban {n_esperados} ResultadoDimension pero se generaron {len(resultados)}"
    )

    psicometricos = [r for r in resultados if r["dominio"] != "Ficha de Datos Generales"]
    assert len(psicometricos) == n_esperados - 1

    niveles_validos = {"SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"}
    for r in psicometricos:
        assert r["dimension"] is not None and r["dimension"] != ""
        assert r["nivel"] in niveles_validos, (
            f"La dimensión {r['dimension']} tiene un nivel no clasificado: {r['nivel']}"
        )
        assert 0.0 <= r["puntajeTransformado"] <= 100.0


# ─── tests ─────────────────────────────────────────────────────────────────

def test_seed_crea_cinco_versiones_con_preguntas_correctas(db_session):
    esperados = {
        "FICHA_DATOS": 22,
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


def test_guardar_ficha_jefatura_asigna_intralaboral_a(client, crear_paciente):
    _, headers_pac, eval_id = _preparar_evaluacion(
        client, crear_paciente, "Empresa FormaA SAS", "Gerencia", "Evaluacion BRP 2026"
    )

    ficha = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Carlos Jefe",
        nombreCargo="Director General",
        tipoCargo=TIPO_CARGO_JEFATURA,
        tienePersonalACargo=True,
    )
    assert ficha["intralaboralAsignado"] == "INTRALABORAL_A"

    codigos_asignados = _codigos_instrumentos(client, headers_pac, eval_id)
    assert "INTRALABORAL_A" in codigos_asignados
    assert "INTRALABORAL_B" not in codigos_asignados


def test_guardar_ficha_auxiliar_asigna_intralaboral_b(client, crear_paciente):
    _, headers_pac, eval_id = _preparar_evaluacion(
        client, crear_paciente, "Empresa FormaB SAS", "Operaciones", "Evaluacion BRP 2026 B"
    )

    ficha = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Ana Auxiliar",
        sexo="Femenino",
        nombreCargo="Auxiliar de Archivo",
        tipoCargo=TIPO_CARGO_AUXILIAR,
        tienePersonalACargo=False,
    )
    assert ficha["intralaboralAsignado"] == "INTRALABORAL_B"

    codigos_asignados = _codigos_instrumentos(client, headers_pac, eval_id)
    assert "INTRALABORAL_B" in codigos_asignados
    assert "INTRALABORAL_A" not in codigos_asignados


def test_participante_no_puede_tener_ambas_formas_intralaboral(client, crear_paciente):
    _, headers_pac, eval_id = _preparar_evaluacion(
        client, crear_paciente, "Empresa CambioCargo SAS", "Planta", "Evaluacion Cambio Cargo"
    )

    # 1. Primero guarda como Jefatura (Forma A)
    ficha1 = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Pedro Cambio",
        nombreCargo="Supervisor",
        tipoCargo=TIPO_CARGO_JEFATURA,
        tienePersonalACargo=True,
    )
    assert ficha1["intralaboralAsignado"] == "INTRALABORAL_A"

    codigos1 = _codigos_instrumentos(client, headers_pac, eval_id)
    assert "INTRALABORAL_A" in codigos1
    assert "INTRALABORAL_B" not in codigos1

    # 2. Ahora actualiza la Ficha a Operario (Forma B)
    ficha2 = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Pedro Cambio",
        nombreCargo="Supervisor",
        tipoCargo=TIPO_CARGO_OPERARIO,
        tienePersonalACargo=False,
    )
    assert ficha2["intralaboralAsignado"] == "INTRALABORAL_B"

    codigos2 = _codigos_instrumentos(client, headers_pac, eval_id)
    assert "INTRALABORAL_B" in codigos2
    assert "INTRALABORAL_A" not in codigos2, (
        "No debe conservar la Forma A si la Ficha cambió a un cargo de Forma B."
    )


def test_get_cuestionario_resuelve_instrumento_real_pendiente(client, crear_paciente):
    """
    Verifica que GET /cuestionario (usado por el Panel) resuelva el instrumento real pendiente
    vía participante_instrumentos (p.ej. ESTRES de 31 preguntas) en lugar de devolver
    el cuestionario de demostración BRP_FORMA_A (de 9 preguntas).
    """
    _, headers_pac, eval_id = _preparar_evaluacion(
        client, crear_paciente, "Empresa PanelSync SAS", "Operaciones", "Evaluación Panel Real 2026"
    )

    # Guardar Ficha de Datos Generales (completa FICHA_DATOS y asigna INTRALABORAL_B)
    ficha = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Pedro Operario",
        nombreCargo="Operario de Producción",
        tipoCargo=TIPO_CARGO_OPERARIO,
        tienePersonalACargo=False,
    )
    assert ficha["intralaboralAsignado"] == "INTRALABORAL_B"

    # Simular Panel llamando GET /cuestionario: DEBE responder ESTRES (31 preguntas), NO BRP_FORMA_A (9 preguntas)
    res_quest = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac)
    assert res_quest.status_code == 200, res_quest.text
    data_quest = res_quest.json()

    assert data_quest["codigo"] == "ESTRES"
    assert data_quest["nombre"] == "Cuestionario para la Evaluación del Estrés"
    preguntas = data_quest["preguntas"]
    assert len(preguntas) == 31, f"Se esperaban 31 preguntas de Estrés, pero llegaron {len(preguntas)}"
    assert preguntas[0]["codigo"] == "EST_1"
    assert preguntas[0]["enunciado"] == "Dolores en el cuello y espalda o tensión muscular."

    # Responder las 31 preguntas de ESTRES y finalizar el instrumento
    res_fin = _responder_y_finalizar(client, headers_pac, eval_id, preguntas)
    assert res_fin["completadoTotal"] is False

    # Siguiente llamada a GET /cuestionario desde el Panel: DEBE responder EXTRALABORAL (31 preguntas)
    res_quest2 = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac)
    assert res_quest2.status_code == 200, res_quest2.text
    data_quest2 = res_quest2.json()

    assert data_quest2["codigo"] == "EXTRALABORAL"
    assert len(data_quest2["preguntas"]) == 31
    assert data_quest2["preguntas"][0]["codigo"] == "EXT_1"


def test_crear_evaluacion_sin_version_id_inicializa_los_5_instrumentos_reales(client, crear_paciente):
    """
    Verifica que la creación por defecto de una evaluación (POST /api/evaluaciones sin versionId en el body)
    inicialice automáticamente los instrumentos reales (FICHA_DATOS, ESTRES, EXTRALABORAL)
    y asigne la Forma Intralaboral B al guardar la Ficha, garantizando que el Panel
    resuelva Estrés (31 preguntas, EST_1) y no BRP_FORMA_A.
    """
    _, headers_pac, eval_id = _preparar_evaluacion(
        client, crear_paciente, "Empresa Default Flow SAS", "Mantenimiento", "Evaluación Flujo Por Defecto 2026"
    )

    # Instrumentos inicializados antes de guardar Ficha (deben ser FICHA_DATOS, ESTRES, EXTRALABORAL)
    res_inst_iniciales = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_pac)
    assert res_inst_iniciales.status_code == 200, res_inst_iniciales.text
    insts_iniciales = res_inst_iniciales.json()

    assert len(insts_iniciales) == 3
    assert insts_iniciales[0]["codigo"] == "FICHA_DATOS" and insts_iniciales[0]["orden"] == 1
    assert insts_iniciales[1]["codigo"] == "ESTRES" and insts_iniciales[1]["orden"] == 2
    assert insts_iniciales[2]["codigo"] == "EXTRALABORAL" and insts_iniciales[2]["orden"] == 3

    # Guardar Ficha con tipoCargo Operario -> debe asignar INTRALABORAL_B como orden 4
    ficha = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Jorge Operario",
        nombreCargo="Técnico Mantenimiento",
        tipoCargo=TIPO_CARGO_OPERARIO,
        tienePersonalACargo=False,
    )
    assert ficha["intralaboralAsignado"] == "INTRALABORAL_B"

    # Verificar que INTRALABORAL_B quedó registrado con orden 4
    res_inst_post_ficha = client.get(f"/api/evaluaciones/{eval_id}/instrumentos", headers=headers_pac)
    assert res_inst_post_ficha.status_code == 200, res_inst_post_ficha.text
    insts_post_ficha = res_inst_post_ficha.json()
    assert len(insts_post_ficha) == 4
    inst_intra = next(i for i in insts_post_ficha if i["codigo"] == "INTRALABORAL_B")
    assert inst_intra["orden"] == 4

    # Simular consulta del Panel (GET /cuestionario): DEBE resolver ESTRES (31 preguntas, EST_1), NO BRP_FORMA_A
    res_panel = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac)
    assert res_panel.status_code == 200, res_panel.text
    data_panel = res_panel.json()

    assert data_panel["codigo"] == "ESTRES"
    assert data_panel["nombre"] == "Cuestionario para la Evaluación del Estrés"
    assert len(data_panel["preguntas"]) == 31
    assert data_panel["preguntas"][0]["codigo"] == "EST_1"
    assert data_panel["preguntas"][0]["enunciado"] == "Dolores en el cuello y espalda o tensión muscular."


def test_flujo_completo_evaluacion_real_tabula_todas_las_dimensiones(client, crear_paciente):
    """
    Prueba E2E real (Etapa 5):
    - Crea una evaluación sin versionId (camino real por defecto).
    - Completa Ficha Datos, Estrés (31), Extralaboral (31) e Intralaboral B (97) mediante la API real.
    - Verifica que se tabulen las 3 dimensiones de los cuestionarios reales y que cada una reciba un nivel de riesgo válido.
    """
    headers_admin, headers_pac, eval_id = _preparar_evaluacion(
        client, crear_paciente, "Empresa E2E Tabulacion SAS", "Logística", "Evaluación E2E BRP Real 2026"
    )

    # Guardar Ficha (asigna INTRALABORAL_B)
    ficha = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Pedro Auxiliar",
        nombreCargo="Auxiliar Bodega",
        tipoCargo=TIPO_CARGO_AUXILIAR,
        tienePersonalACargo=False,
    )
    assert ficha["intralaboralAsignado"] == "INTRALABORAL_B"

    # Responder y finalizar secuencialmente: ESTRES, EXTRALABORAL, INTRALABORAL_B
    completados, final_res = _completar_instrumentos(client, headers_pac, eval_id)
    assert completados == 3
    assert final_res["completadoTotal"] is True

    # Intralaboral B: dimensiones + dominios + 1 total del cuestionario, tomado de la misma
    # referencia oficial (Tablas 21-34) que usa el sembrado real.
    ref_b = cargar_referencia()["forma_B"]
    n_intralaboral_b = len(ref_b["dimensiones"]) + len(ref_b["dominios"]) + 1
    _verificar_resultados_tabulados(client, headers_admin, eval_id, n_intralaboral_b)


def test_flujo_completo_evaluacion_real_tabula_todas_las_dimensiones_forma_a(client, crear_paciente):
    """
    Misma prueba E2E que test_flujo_completo_evaluacion_real_tabula_todas_las_dimensiones,
    pero con un participante Jefatura/Profesional (Intralaboral Forma A) en vez de Auxiliar
    (Forma B). Cubre la otra mitad de la estructura real: 19 dimensiones + 4 dominios + 1
    total de Forma A, que la prueba de Forma B no ejercita.
    """
    headers_admin, headers_pac, eval_id = _preparar_evaluacion(
        client, crear_paciente, "Empresa E2E Tabulacion Forma A SAS", "Gerencia", "Evaluación E2E BRP Real Forma A 2026"
    )

    # Guardar Ficha con tipoCargo de Jefatura (asigna INTRALABORAL_A)
    ficha = _guardar_ficha(
        client, headers_pac, eval_id,
        nombreCompleto="Carlos Jefe",
        nombreCargo="Director General",
        tipoCargo=TIPO_CARGO_JEFATURA,
        tienePersonalACargo=True,
    )
    assert ficha["intralaboralAsignado"] == "INTRALABORAL_A"

    # Responder y finalizar secuencialmente: ESTRES, EXTRALABORAL, INTRALABORAL_A
    completados, final_res = _completar_instrumentos(client, headers_pac, eval_id)
    assert completados == 3
    assert final_res["completadoTotal"] is True

    # Intralaboral A: 19 dimensiones + 4 dominios + 1 total = 24, calculado contra la referencia oficial.
    ref_a = cargar_referencia()["forma_A"]
    n_intralaboral_a = len(ref_a["dimensiones"]) + len(ref_a["dominios"]) + 1
    _verificar_resultados_tabulados(client, headers_admin, eval_id, n_intralaboral_a)