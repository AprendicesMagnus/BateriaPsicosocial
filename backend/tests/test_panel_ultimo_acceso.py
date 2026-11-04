import io
import uuid
from datetime import datetime, timedelta, timezone

import openpyxl

from app.models.audit import Auditoria
from app.models.user import Usuario
from app.services.panel import TIPO_POR_ACCION


def _login_admin(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def test_ultimo_acceso_cuenta_login_2fa(client, db_session):
    headers = _login_admin(client)
    admin = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin is not None

    futuro = datetime.now(timezone.utc) + timedelta(days=1)
    db_session.add(
        Auditoria(id=uuid.uuid4(), usuario_id=admin.id, accion="LOGIN_2FA", registrado_en=futuro)
    )
    db_session.commit()

    res = client.get("/api/panel", headers=headers)
    assert res.status_code == 200, res.text
    fila = next(u for u in res.json()["usuarios"] if u["correo"] == "admin@magnussig.com")
    assert fila["ultimoAcceso"] is not None

    recibido = datetime.fromisoformat(fila["ultimoAcceso"])
    if recibido.tzinfo is None:
        recibido = recibido.replace(tzinfo=timezone.utc)
    else:
        recibido = recibido.astimezone(timezone.utc)
    # El LOGIN real de esta prueba es anterior: el ultimo acceso debe ser el LOGIN_2FA futuro
    assert abs((recibido - futuro).total_seconds()) < 1


def test_tipo_de_acciones_nuevas_en_el_filtro_del_panel():
    assert TIPO_POR_ACCION["LOGIN_2FA"] == "Accesos"
    assert TIPO_POR_ACCION["INFORMES_EXCEL_DESCARGADOS"] == "Resultados"


def test_exportar_auditoria_etiquetas_login_2fa_e_informes_excel(client, db_session):
    headers = _login_admin(client)
    admin = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin is not None

    ahora = datetime.now(timezone.utc)
    nota_2fa = f"etiqueta-2fa-{uuid.uuid4().hex[:6]}"
    nota_xls = f"etiqueta-xls-{uuid.uuid4().hex[:6]}"
    db_session.add_all([
        Auditoria(id=uuid.uuid4(), usuario_id=admin.id, accion="LOGIN_2FA", nota=nota_2fa, registrado_en=ahora),
        Auditoria(id=uuid.uuid4(), usuario_id=admin.id, accion="INFORMES_EXCEL_DESCARGADOS", nota=nota_xls, registrado_en=ahora),
    ])
    db_session.commit()

    res = client.get("/api/panel/exportar/auditoria", headers=headers)
    assert res.status_code == 200, res.text
    ws = openpyxl.load_workbook(io.BytesIO(res.content)).active
    filas = list(ws.iter_rows(min_row=2, values_only=True))
    fila_2fa = next((f for f in filas if f[4] == nota_2fa), None)
    fila_xls = next((f for f in filas if f[4] == nota_xls), None)

    assert fila_2fa is not None and fila_xls is not None
    assert fila_2fa[2] == "inició sesión con verificación en dos pasos"
    assert fila_xls[2] == "descargó informes en Excel"
