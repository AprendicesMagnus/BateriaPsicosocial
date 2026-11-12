import uuid

import pytest

from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios


FICHA_SEGUIMIENTO = {
    "nombreCompleto": "Paciente de prueba",
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
    "tienePersonalACargo": False,
}


@pytest.fixture(autouse=True)
def seed_cuestionarios(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def test_superadmin_consulta_seguimiento_por_empresa_usuario_y_movimiento(client, acreditar_baterias):
    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert admin_login.status_code == 200, admin_login.text
    headers_admin = {"Authorization": f"Bearer {admin_login.json()['token']}"}

    nit_base = f"8{str(uuid.uuid4().int)[:8]}"
    empresa = client.post(
        "/api/organizaciones",
        headers=headers_admin,
        json={"nombre": "Empresa Seguimiento", "nit": f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"},
    )
    assert empresa.status_code in (200, 201), empresa.text
    empresa_id = empresa.json()["id"]

    email = f"seguimiento_{uuid.uuid4().hex[:8]}@test.com"
    usuario = client.post(
        "/api/usuarios",
        headers=headers_admin,
        json={
            "nombre": "Laura",
            "apellido": "Psicóloga",
            "email": email,
            "password": "Evaluador1234",
            "rolCodigo": "EVALUADOR_SST",
            "organizacionId": empresa_id,
        },
    )
    assert usuario.status_code in (200, 201), usuario.text
    usuario_id = usuario.json()["id"]
    acreditar_baterias(empresa_id, usuario_id, cantidad=2)

    login_psico = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Evaluador1234"},
    )
    assert login_psico.status_code == 200, login_psico.text
    headers_psico = {"Authorization": f"Bearer {login_psico.json()['token']}"}

    enlace = client.post(
        "/api/enlaces",
        headers=headers_psico,
        json={"nombre": "Enlace de seguimiento"},
    )
    assert enlace.status_code == 200, enlace.text
    inicio = client.post(
        f"/api/enlaces/publico/{enlace.json()['token']}/iniciar",
        json={"aceptaConsentimiento": True},
    )
    assert inicio.status_code == 200, inicio.text
    headers_paciente = {"Authorization": f"Bearer {inicio.json()['token']}"}
    respuesta = client.post(
        f"/api/evaluaciones/{inicio.json()['evaluacionId']}/ficha",
        headers=headers_paciente,
        json=FICHA_SEGUIMIENTO,
    )
    assert respuesta.status_code == 200, respuesta.text

    seguimiento = client.get("/api/panel/seguimiento-baterias", headers=headers_admin)
    assert seguimiento.status_code == 200, seguimiento.text
    datos = seguimiento.json()

    fila_empresa = next(e for e in datos["empresas"] if e["id"] == empresa_id)
    assert fila_empresa["compradas"] == 2
    assert fila_empresa["consumidas"] == 1
    assert fila_empresa["disponibles"] == 1

    fila_usuario = next(u for u in datos["usuarios"] if u["id"] == usuario_id and u["empresaId"] == empresa_id)
    assert fila_usuario["compradas"] == 2
    assert fila_usuario["consumidas"] == 1
    assert fila_usuario["disponiblesEmpresa"] == 1

    assert any(m["tipo"] == "COMPRA" and m["cantidad"] == 2 for m in datos["movimientos"])
    assert any(m["tipo"] == "CONSUMO" and m["cantidad"] == -1 for m in datos["movimientos"])
