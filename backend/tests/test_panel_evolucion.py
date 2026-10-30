import uuid
from datetime import datetime, timezone

from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.commercial import Compra
from app.models.organization import Organizacion


def test_evolucion_panel_completo(client, db_session, crear_paciente):
    # 1. Login Super Administrador
    res_admin = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # a) GET /api/panel/evolucion devuelve 200 y 12 elementos, ordenados, con las 5 claves numéricas en cada uno
    res = client.get("/api/panel/evolucion", headers=headers_admin)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "meses" in data
    meses = data["meses"]
    assert len(meses) == 12

    claves_numericas = [
        "usuariosNuevos",
        "evaluacionesCreadas",
        "encuestasCompletadas",
        "comprasPagadas",
        "valorComprado",
    ]

    for item in meses:
        assert "mes" in item
        assert "etiqueta" in item
        for k in claves_numericas:
            assert k in item
            assert isinstance(item[k], (int, float))

    meses_codigos = [item["mes"] for item in meses]
    assert meses_codigos == sorted(meses_codigos), "Los meses deben estar ordenados cronológicamente"

    # b) Con una Compra PAGADA creada en el mes actual, comprasPagadas y valorComprado del último mes aumentan
    ultimo_antes = meses[-1]
    cp_antes = ultimo_antes["comprasPagadas"]
    vc_antes = ultimo_antes["valorComprado"]

    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Test Evolucion SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()

    from app.models.user import Usuario

    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    compra_nueva = Compra(
        id=uuid.uuid4(),
        usuario_id=admin_user.id,
        organizacion_id=org.id,
        cantidad=10,
        subtotal=100000.0,
        iva=20000.0,
        total=120000,
        estado="PAGADA",
        creado_en=datetime.now(timezone.utc),
    )
    db_session.add(compra_nueva)
    db_session.commit()

    res_despues = client.get("/api/panel/evolucion", headers=headers_admin)
    assert res_despues.status_code == 200, res_despues.text
    ultimo_despues = res_despues.json()["meses"][-1]

    assert ultimo_despues["comprasPagadas"] == cp_antes + 10
    assert ultimo_despues["valorComprado"] == vc_antes + 120000

    # c) Un usuario sin token recibe 401 o 403, y uno que no es SUPER_ADMINISTRADOR recibe 403
    res_sin_token = client.get("/api/panel/evolucion")
    assert res_sin_token.status_code in (401, 403), res_sin_token.text

    _pid, email_paciente = crear_paciente(org.id, password="Paciente123!")
    res_login_p = client.post(
        "/api/auth/login",
        json={"email": email_paciente, "password": "Paciente123!"},
    )
    assert res_login_p.status_code == 200, res_login_p.text
    headers_paciente = {"Authorization": f"Bearer {res_login_p.json()['token']}"}

    res_no_admin = client.get("/api/panel/evolucion", headers=headers_paciente)
    assert res_no_admin.status_code == 403, res_no_admin.text

    # d) meses=2 o meses=30 devuelve 422
    res_min = client.get("/api/panel/evolucion?meses=2", headers=headers_admin)
    assert res_min.status_code == 422, res_min.text

    res_max = client.get("/api/panel/evolucion?meses=30", headers=headers_admin)
    assert res_max.status_code == 422, res_max.text
