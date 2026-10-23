import uuid
from datetime import datetime, timezone

from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.commercial import Compra
from app.models.evaluation import EvaluacionParticipante
from app.models.organization import Organizacion
from app.models.user import Usuario


def _login_admin(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _obtener_punto_mes_actual(client, headers, meses=12):
    mes_str = datetime.now(timezone.utc).strftime("%Y-%m")
    res = client.get(f"/api/panel/evolucion?meses={meses}", headers=headers)
    assert res.status_code == 200, res.text
    for p in res.json()["meses"]:
        if p["mes"] == mes_str:
            return p
    assert False, f"Mes actual {mes_str} no encontrado en evolución con meses={meses}"


def _verificar_meses_consecutivos(lista_puntos):
    lista_meses = [p["mes"] for p in lista_puntos]
    for i in range(len(lista_meses) - 1):
        y1, m1 = map(int, lista_meses[i].split("-"))
        y2, m2 = map(int, lista_meses[i + 1].split("-"))
        if m1 == 12:
            assert y2 == y1 + 1 and m2 == 1, f"Hueco cronológico entre {lista_meses[i]} y {lista_meses[i+1]}"
        else:
            assert y2 == y1 and m2 == m1 + 1, f"Hueco cronológico entre {lista_meses[i]} y {lista_meses[i+1]}"


def _verificar_metricas_puntos(lista_puntos):
    claves = ["usuariosNuevos", "evaluacionesCreadas", "encuestasCompletadas", "comprasPagadas", "valorComprado"]
    for p in lista_puntos:
        for k in claves:
            assert k in p, f"Falta clave {k} en punto {p}"
            assert isinstance(p[k], int) and type(p[k]) is not bool, f"Clave {k} debe ser int en {p}"
            assert p[k] >= 0, f"Clave {k} debe ser >= 0 en {p}"


def test_evolucion_estructura_y_ceros(client):
    # (a) Estructura y ceros: meses=3 y meses=24, consecutivos, sin huecos, métricas enteras >= 0
    headers = _login_admin(client)

    res3 = client.get("/api/panel/evolucion?meses=3", headers=headers)
    assert res3.status_code == 200, res3.text
    puntos3 = res3.json()["meses"]
    assert len(puntos3) == 3
    _verificar_meses_consecutivos(puntos3)
    _verificar_metricas_puntos(puntos3)

    res24 = client.get("/api/panel/evolucion?meses=24", headers=headers)
    assert res24.status_code == 200, res24.text
    puntos24 = res24.json()["meses"]
    assert len(puntos24) == 24
    _verificar_meses_consecutivos(puntos24)
    _verificar_metricas_puntos(puntos24)


def test_evolucion_usuarios_nuevos_excluye_invitados(client, db_session, crear_paciente):
    # (b) usuariosNuevos: paciente no invitado (+1) vs invitado (+0)
    headers = _login_admin(client)
    antes = _obtener_punto_mes_actual(client, headers)["usuariosNuevos"]

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Ev Usuarios SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()

    # Paciente con password -> no invitado
    crear_paciente(org.id, password="Password123!")
    # Paciente sin password -> invitado
    crear_paciente(org.id)

    despues = _obtener_punto_mes_actual(client, headers)["usuariosNuevos"]
    assert despues - antes == 1, f"Se esperaba diferencia +1, fue {despues - antes}"


def test_evolucion_evaluaciones_creadas(client, db_session, crear_paciente):
    # (c) evaluacionesCreadas: evaluacion creada por API suma exactamente +1 en mes actual
    headers = _login_admin(client)
    antes = _obtener_punto_mes_actual(client, headers)["evaluacionesCreadas"]

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Ev Evaluaciones SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()

    res_cuest = client.get("/api/cuestionarios", headers=headers)
    assert res_cuest.status_code == 200
    version_id = res_cuest.json()[0]["id"]

    pid, _ = crear_paciente(org.id, password="Paciente123!")

    res_eval = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "organizacionId": str(org.id),
            "nombre": f"Evaluación Cobertura {uuid.uuid4().hex[:6]}",
            "versionId": version_id,
            "trabajadoresIds": [str(pid)],
        },
    )
    assert res_eval.status_code == 200, res_eval.text

    despues = _obtener_punto_mes_actual(client, headers)["evaluacionesCreadas"]
    assert despues - antes == 1, f"Se esperaba diferencia +1 en evaluacionesCreadas, fue {despues - antes}"


def test_evolucion_encuestas_completadas_requiere_fecha_fin(client, db_session, crear_paciente):
    # (d) encuestasCompletadas: solo COMPLETADA con fecha_fin cuenta; COMPLETADA con fecha_fin nula no cuenta
    headers = _login_admin(client)
    antes = _obtener_punto_mes_actual(client, headers)["encuestasCompletadas"]

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Ev Encuestas SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()

    res_cuest = client.get("/api/cuestionarios", headers=headers)
    assert res_cuest.status_code == 200
    version_id = res_cuest.json()[0]["id"]

    p1, _ = crear_paciente(org.id, password="PacienteP1!")
    p2, _ = crear_paciente(org.id, password="PacienteP2!")

    res_eval = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "organizacionId": str(org.id),
            "nombre": f"Evaluación Participantes {uuid.uuid4().hex[:6]}",
            "versionId": version_id,
            "trabajadoresIds": [str(p1), str(p2)],
        },
    )
    assert res_eval.status_code == 200, res_eval.text
    eval_id = uuid.UUID(res_eval.json()["id"])

    parts = db_session.query(EvaluacionParticipante).filter(EvaluacionParticipante.evaluacion_id == eval_id).all()
    assert len(parts) == 2

    # Participante COMPLETADA con fecha_fin nula NO debe contarse
    parts[0].estado = "COMPLETADA"
    parts[0].fecha_fin = None
    db_session.commit()

    intermedio = _obtener_punto_mes_actual(client, headers)["encuestasCompletadas"]
    assert intermedio == antes, "Participante COMPLETADA con fecha_fin nula NO debe contarse"

    # Al asignarle fecha_fin ahora (UTC), sí cuenta
    ahora = datetime.now(timezone.utc)
    parts[0].fecha_fin = ahora
    # parts[1] queda sin completar
    parts[1].estado = "PENDIENTE"
    parts[1].fecha_fin = None
    db_session.commit()

    despues = _obtener_punto_mes_actual(client, headers)["encuestasCompletadas"]
    assert despues - antes == 1, f"Se esperaba diferencia +1 en encuestasCompletadas, fue {despues - antes}"


def test_evolucion_registro_antiguo_aparece_en_24_no_en_12(client, db_session):
    # (e) Registro de hace 14 meses NO aparece en meses=12 y SÍ aparece en meses=24
    headers = _login_admin(client)
    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Ev Compra 14M SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()

    suma_12_antes = sum(p["comprasPagadas"] for p in client.get("/api/panel/evolucion?meses=12", headers=headers).json()["meses"])
    suma_24_antes = sum(p["comprasPagadas"] for p in client.get("/api/panel/evolucion?meses=24", headers=headers).json()["meses"])

    ahora = datetime.now(timezone.utc)
    m_ant = ahora.month - 14
    y_ant = ahora.year
    while m_ant <= 0:
        m_ant += 12
        y_ant -= 1
    fecha_14m = datetime(y_ant, m_ant, 15, tzinfo=timezone.utc)

    compra = Compra(
        id=uuid.uuid4(),
        usuario_id=admin_user.id,
        organizacion_id=org.id,
        cantidad=7,
        subtotal=70000.0,
        iva=13300.0,
        total=83300.0,
        estado="PAGADA",
        creado_en=fecha_14m,
    )
    db_session.add(compra)
    db_session.commit()

    suma_12_despues = sum(p["comprasPagadas"] for p in client.get("/api/panel/evolucion?meses=12", headers=headers).json()["meses"])
    suma_24_despues = sum(p["comprasPagadas"] for p in client.get("/api/panel/evolucion?meses=24", headers=headers).json()["meses"])

    assert suma_12_despues == suma_12_antes, "El registro de hace 14 meses NO debe aparecer en ventana de 12 meses"
    assert suma_24_despues == suma_24_antes + 7, f"El registro de hace 14 meses SÍ debe sumar +7 en ventana de 24 meses (fue {suma_24_despues - suma_24_antes})"
