import uuid

import pytest

from app.core.crypto import hash_password
from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Organizacion, Area
from app.models.survey import CuestionarioVersion, Dimension
from app.models.user import Rol, Usuario


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


def _crear_usuario_con_rol(db_session, codigo_rol, organizacion_id, password="Test1234!"):
    rol = db_session.query(Rol).filter(Rol.codigo == codigo_rol).first()
    assert rol is not None, f"El rol {codigo_rol} no está sembrado."
    email = f"{codigo_rol.lower()}_{uuid.uuid4().hex[:8]}@test.com"
    usuario = Usuario(
        nombre="Usuario",
        apellido="Prueba",
        email=email,
        password_hash=hash_password(password),
        rol_id=rol.id,
        estado="ACTIVO",
        email_verificado=True,
        organizacion_id=uuid.UUID(str(organizacion_id)),
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario.id, email


def _crear_org_con_datos(client, db_session, headers_admin, crear_paciente):
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Permisos SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()
    org_id = org.id

    area = Area(id=uuid.uuid4(), organizacion_id=org_id, nombre="Operaciones")
    db_session.add(area)
    db_session.commit()

    dim = db_session.query(Dimension).first()
    assert dim is not None
    cuestionario = db_session.query(CuestionarioVersion).filter(
        CuestionarioVersion.id == dim.version_id
    ).first()

    from app.models.user import Usuario as _Usuario
    admin_user = db_session.query(_Usuario).filter(_Usuario.email == "admin@magnussig.com").first()

    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        organizacion_id=org_id,
        evaluador_id=admin_user.id,
        nombre="Evaluación Permisos 2026",
    )
    db_session.add(evaluacion)
    db_session.commit()

    for _ in range(5):
        p_id = crear_paciente(org_id, area_id=area.id)[0]
        part = EvaluacionParticipante(
            id=uuid.uuid4(),
            evaluacion_id=evaluacion.id,
            trabajador_id=p_id,
            estado="COMPLETADA",
        )
        db_session.add(part)
        db_session.flush()
        db_session.add(ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=50.0,
            puntaje_transformado=50.0,
            nivel="MEDIO",
        ))

    db_session.commit()
    return org_id, cuestionario.codigo


def _login(client, email, password="Test1234!"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def test_jefe_puede_ver_mapa_calor_e_historico(client, db_session, crear_paciente):
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    org_id, codigo = _crear_org_con_datos(client, db_session, headers_admin, crear_paciente)
    _uid, email = _crear_usuario_con_rol(db_session, "JEFE", org_id)
    headers = _login(client, email)

    res_mapa = client.get(f"/api/indicadores/mapa-calor?organizacion_id={org_id}&codigo={codigo}", headers=headers)
    assert res_mapa.status_code == 200, res_mapa.text

    res_hist = client.get(f"/api/indicadores/historico?organizacion_id={org_id}", headers=headers)
    assert res_hist.status_code == 200, res_hist.text


def test_administrador_puede_ver_mapa_calor_e_historico(client, db_session, crear_paciente):
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    org_id, codigo = _crear_org_con_datos(client, db_session, headers_admin, crear_paciente)
    _uid, email = _crear_usuario_con_rol(db_session, "ADMINISTRADOR", org_id)
    headers = _login(client, email)

    res_mapa = client.get(f"/api/indicadores/mapa-calor?organizacion_id={org_id}&codigo={codigo}", headers=headers)
    assert res_mapa.status_code == 200, res_mapa.text

    res_hist = client.get(f"/api/indicadores/historico?organizacion_id={org_id}", headers=headers)
    assert res_hist.status_code == 200, res_hist.text


def test_jefe_y_administrador_no_pueden_ver_grupos(client, db_session, crear_paciente):
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    org_id, codigo = _crear_org_con_datos(client, db_session, headers_admin, crear_paciente)

    for codigo_rol in ("JEFE", "ADMINISTRADOR"):
        _uid, email = _crear_usuario_con_rol(db_session, codigo_rol, org_id)
        headers = _login(client, email)
        res = client.get(f"/api/indicadores/grupos?organizacion_id={org_id}", headers=headers)
        assert res.status_code == 403, f"El rol {codigo_rol} debería recibir 403 en /grupos pero obtuvo {res.status_code}"


def test_paciente_no_puede_ver_historico_ni_mapa_calor(client, db_session, crear_paciente):
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    org_id, codigo = _crear_org_con_datos(client, db_session, headers_admin, crear_paciente)

    password = "Paciente1234!"
    _uid, email = crear_paciente(org_id, password=password)
    headers = _login(client, email, password)

    res_hist = client.get(f"/api/indicadores/historico?organizacion_id={org_id}", headers=headers)
    assert res_hist.status_code == 403, res_hist.text

    res_mapa = client.get(f"/api/indicadores/mapa-calor?organizacion_id={org_id}&codigo={codigo}", headers=headers)
    assert res_mapa.status_code == 403, res_mapa.text


def test_jefe_solo_recibe_datos_de_su_organizacion(client, db_session, crear_paciente):
    res_admin = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    org_id_propia, _codigo = _crear_org_con_datos(client, db_session, headers_admin, crear_paciente)
    org_id_ajena, _codigo2 = _crear_org_con_datos(client, db_session, headers_admin, crear_paciente)

    _uid, email = _crear_usuario_con_rol(db_session, "JEFE", org_id_propia)
    headers = _login(client, email)

    res = client.get(f"/api/indicadores/historico?organizacion_id={org_id_ajena}", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert str(data["organizacionId"]) == str(org_id_propia), (
        "El JEFE debe recibir solo datos de su propia organización, "
        f"pero organizacionId devuelto fue {data['organizacionId']}"
    )
