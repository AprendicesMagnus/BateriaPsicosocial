"""
Pruebas de los enlaces para pacientes:
- El psicólogo (EVALUADOR_SST) crea un enlace y lo ve en su lista.
- El paciente inicia sin cuenta, llena la Ficha (que da su nombre) y sigue con Estrés.
- El psicólogo ve al paciente en "Encuestas realizadas" con el nombre de la Ficha.
- El invitado no puede iniciar sesión con correo/contraseña.
"""
import uuid

import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios

FICHA = {
    "nombreCompleto": "Ana Paciente",
    "sexo": "Femenino",
    "anioNacimiento": "1990",
    "estadoCivil": "Soltero (a)",
    "nivelEstudios": "Profesional completo",
    "ocupacion": "Contadora",
    "residenciaCiudad": "Neiva",
    "residenciaDepartamento": "Huila",
    "estrato": "3",
    "tipoVivienda": "Familiar",
    "personasACargo": 0,
    "trabajoCiudad": "Neiva",
    "trabajoDepartamento": "Huila",
    "antiguedadEmpresaMenosUnAnio": True,
    "antiguedadEmpresa": "0",
    "nombreCargo": "Contadora",
    "tipoCargo": "Profesional, analista, técnico, tecnólogo",
    "antiguedadCargoMenosUnAnio": True,
    "antiguedadCargo": "0",
    "areaODepartamento": "Finanzas",
    "tipoContrato": "Indefinido",
    "horasDiarias": 8,
    "tipoSalario": "Fijo",
}


@pytest.fixture(autouse=True)
def setup_seed_instrumentos(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def _psicologo(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    res_org = client.post(
        "/api/organizaciones",
        headers=headers_admin,
        json={"nombre": "Consultorio Enlaces", "nit": f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"},
    )
    org_id = res_org.json()["id"]
    email = f"psico_{uuid.uuid4().hex[:6]}@test.com"
    res_user = client.post(
        "/api/usuarios",
        headers=headers_admin,
        json={
            "nombre": "Laura",
            "apellido": "Psicóloga",
            "email": email,
            "password": "Evaluador1234",
            "rolCodigo": "EVALUADOR_SST",
            "organizacionId": org_id,
        },
    )
    assert res_user.status_code in (200, 201), res_user.text
    res_login = client.post("/api/auth/login", json={"email": email, "password": "Evaluador1234"})
    assert res_login.status_code == 200, res_login.text
    return {"Authorization": f"Bearer {res_login.json()['token']}"}


def test_flujo_completo_enlace_paciente(client):
    headers_psico = _psicologo(client)

    # 1. El psicólogo crea el enlace y lo ve en su lista
    res = client.post("/api/enlaces", headers=headers_psico, json={"nombre": "Pacientes septiembre"})
    assert res.status_code == 200, res.text
    enlace = res.json()
    token = enlace["token"]
    assert token and enlace["estado"] == "EN_CURSO"

    lista = client.get("/api/enlaces", headers=headers_psico).json()
    # Nadie lo ha abierto todavía
    assert next(e for e in lista if e["token"] == token)["paciente"] is None

    # 2. El paciente abre el enlace sin sesión
    info = client.get(f"/api/enlaces/publico/{token}")
    assert info.status_code == 200
    assert info.json()["activo"] is True

    # Sin aceptar el consentimiento no puede empezar
    rechazo = client.post(f"/api/enlaces/publico/{token}/iniciar", json={"aceptaConsentimiento": False})
    assert rechazo.status_code == 400

    inicio = client.post(f"/api/enlaces/publico/{token}/iniciar", json={"aceptaConsentimiento": True})
    assert inicio.status_code == 200, inicio.text
    datos = inicio.json()
    assert datos["usuario"]["esInvitado"] is True
    eval_id = datos["evaluacionId"]
    headers_pac = {"Authorization": f"Bearer {datos['token']}"}

    # 3. Lo primero pendiente es la Ficha de datos
    cuestionario = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac).json()
    assert cuestionario["codigo"] == "FICHA_DATOS"

    res_ficha = client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_pac, json=FICHA)
    assert res_ficha.status_code == 200, res_ficha.text

    # 4. Después de la Ficha sigue Estrés
    cuestionario = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac).json()
    assert cuestionario["codigo"] == "ESTRES"

    # 5. En la lista de enlaces aparece el paciente con el nombre de la Ficha
    enlace = next(e for e in client.get("/api/enlaces", headers=headers_psico).json() if e["token"] == token)
    assert enlace["paciente"] == {"nombre": "Ana Paciente", "estado": "EN_PROGRESO"}

    # El psicólogo ve al paciente con el nombre de la Ficha y sin el correo interno
    encuestas = client.get("/api/reportes/encuestas", headers=headers_psico).json()
    del_enlace = [e for e in encuestas if e["evaluacionId"] == eval_id]
    assert len(del_enlace) == 1
    assert del_enlace[0]["trabajadorNombre"] == "Ana Paciente"
    assert del_enlace[0]["trabajadorEmail"] is None
    assert del_enlace[0]["viaEnlace"] is True

    # 6. El invitado no puede iniciar sesión con correo/contraseña
    me = client.get("/api/auth/me", headers=headers_pac).json()["usuario"]
    login = client.post("/api/auth/login", json={"email": me["email"], "password": "cualquiera"})
    assert login.status_code == 401


def _iniciar_paciente(client, headers_psico):
    token = client.post("/api/enlaces", headers=headers_psico, json={"nombre": "Enlace único"}).json()["token"]
    datos = client.post(f"/api/enlaces/publico/{token}/iniciar", json={"aceptaConsentimiento": True}).json()
    return token, datos["evaluacionId"], {"Authorization": f"Bearer {datos['token']}"}


def test_enlace_es_de_un_solo_paciente(client):
    headers_psico = _psicologo(client)
    token, _, _ = _iniciar_paciente(client, headers_psico)

    assert client.get(f"/api/enlaces/publico/{token}").json()["enUso"] is True
    # Empezó pero aún no llena la Ficha: se sabe que hay paciente, no quién es
    enlace = next(e for e in client.get("/api/enlaces", headers=headers_psico).json() if e["token"] == token)
    assert enlace["paciente"] == {"nombre": None, "estado": "PENDIENTE"}
    # Otra persona con el mismo enlace no puede empezar
    otro = client.post(f"/api/enlaces/publico/{token}/iniciar", json={"aceptaConsentimiento": True})
    assert otro.status_code == 400


def test_enlace_se_cierra_al_terminar_la_bateria(client):
    headers_psico = _psicologo(client)
    token, eval_id, headers_pac = _iniciar_paciente(client, headers_psico)
    assert client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_pac, json=FICHA).status_code == 200

    # Responde todos los instrumentos pendientes (Estrés, Extralaboral, Intralaboral) con el valor mínimo
    final = None
    for _ in range(5):
        cuestionario = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac).json()
        if cuestionario["codigo"] is None:
            break
        for p in cuestionario["preguntas"]:
            res = client.post(
                f"/api/evaluaciones/{eval_id}/respuestas",
                headers=headers_pac,
                json={"preguntaId": p["id"], "valor": p["valorMinimo"]},
            )
            assert res.status_code == 200, res.text
        final = client.post(f"/api/evaluaciones/{eval_id}/finalizar-cuestionario", headers=headers_pac, json={})
        assert final.status_code == 200, final.text
    assert final.json()["completadoTotal"] is True

    # El enlace quedó cerrado: ya no está activo y nadie más puede empezar
    info = client.get(f"/api/enlaces/publico/{token}").json()
    assert info["activo"] is False
    lista = client.get("/api/enlaces", headers=headers_psico).json()
    assert next(e for e in lista if e["token"] == token)["estado"] == "FINALIZADA"
    otro = client.post(f"/api/enlaces/publico/{token}/iniciar", json={"aceptaConsentimiento": True})
    assert otro.status_code == 400


def test_eliminar_enlace_sin_usar_lo_borra(client):
    headers_psico = _psicologo(client)
    enlace = client.post("/api/enlaces", headers=headers_psico, json={"nombre": "Sin usar"}).json()

    res = client.delete(f"/api/enlaces/{enlace['evaluacionId']}", headers=headers_psico)
    assert res.status_code == 200, res.text
    assert all(e["token"] != enlace["token"] for e in client.get("/api/enlaces", headers=headers_psico).json())
    # La evaluación vacía se borró: el enlace ya no funciona
    assert client.get(f"/api/enlaces/publico/{enlace['token']}").status_code == 404
    # Eliminarlo otra vez da 404
    assert client.delete(f"/api/enlaces/{enlace['evaluacionId']}", headers=headers_psico).status_code == 404


def test_eliminar_enlace_usado_conserva_la_encuesta(client):
    headers_psico = _psicologo(client)
    token, eval_id, headers_pac = _iniciar_paciente(client, headers_psico)
    client.post(f"/api/evaluaciones/{eval_id}/ficha", headers=headers_pac, json=FICHA)

    assert client.delete(f"/api/enlaces/{eval_id}", headers=headers_psico).status_code == 200
    # Sale de la lista de enlaces...
    assert all(e["token"] != token for e in client.get("/api/enlaces", headers=headers_psico).json())
    # ...pero la encuesta sigue en Reportes y el paciente puede seguir respondiendo
    encuestas = client.get("/api/reportes/encuestas", headers=headers_psico).json()
    assert any(e["evaluacionId"] == eval_id and e["trabajadorNombre"] == "Ana Paciente" for e in encuestas)
    cuestionario = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_pac).json()
    assert cuestionario["codigo"] == "ESTRES"


def test_limpieza_automatica_vacia_la_lista(client, db_session):
    from app.services.enlaces import limpiar_enlaces

    headers_psico = _psicologo(client)
    client.post("/api/enlaces", headers=headers_psico, json={"nombre": "Para limpiar"})
    _, eval_id, _ = _iniciar_paciente(client, headers_psico)
    assert len(client.get("/api/enlaces", headers=headers_psico).json()) == 2

    assert limpiar_enlaces(db_session) >= 2
    assert client.get("/api/enlaces", headers=headers_psico).json() == []
    # La encuesta del paciente sigue en Reportes
    encuestas = client.get("/api/reportes/encuestas", headers=headers_psico).json()
    assert any(e["evaluacionId"] == eval_id for e in encuestas)


def test_enlace_inexistente_y_sin_permisos(client):
    assert client.get("/api/enlaces/publico/no-existe").status_code == 404
    # Sin sesión no se pueden crear enlaces
    assert client.post("/api/enlaces", json={"nombre": "X enlace"}).status_code == 401
