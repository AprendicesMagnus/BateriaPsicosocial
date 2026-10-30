import io
import uuid
from datetime import datetime, timezone
import openpyxl

from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.audit import Auditoria
from app.models.organization import Organizacion
from app.models.user import Usuario


def test_exportar_auditoria_nombre_invitado_es_sistema(client, db_session, crear_paciente):
    # 1. Login admin
    res_admin = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res_admin.status_code == 200
    headers = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear organización
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Invitados SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()

    # 3. Crear invitado sin password (es_invitado=True)
    invitado_id, _ = crear_paciente(org.id)

    # 4. Obtener admin
    admin_user = db_session.query(Usuario).filter(Usuario.email == "admin@magnussig.com").first()
    assert admin_user is not None

    # 5. Insertar auditorias
    ahora = datetime.now(timezone.utc)
    aud_invitado = Auditoria(
        id=uuid.uuid4(),
        usuario_id=invitado_id,
        accion="INICIAR_EVALUACION",
        nota="evento-invitado-3e",
        registrado_en=ahora,
    )
    aud_admin = Auditoria(
        id=uuid.uuid4(),
        usuario_id=admin_user.id,
        accion="INICIAR_EVALUACION",
        nota="evento-admin-3e",
        registrado_en=ahora,
    )
    db_session.add_all([aud_invitado, aud_admin])
    db_session.commit()

    # 6. GET /api/panel/exportar/auditoria
    res = client.get("/api/panel/exportar/auditoria", headers=headers)
    assert res.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(res.content))
    ws = wb.active

    filas = list(ws.iter_rows(min_row=2, values_only=True))

    fila_invitado = None
    fila_admin = None
    for f in filas:
        if f[4] == "evento-invitado-3e":
            fila_invitado = f
        elif f[4] == "evento-admin-3e":
            fila_admin = f

    assert fila_invitado is not None, "No se encontró la fila con detalle 'evento-invitado-3e'"
    assert fila_admin is not None, "No se encontró la fila con detalle 'evento-admin-3e'"

    assert fila_invitado[1] == "Sistema", f"Usuario para invitado debe ser 'Sistema', se obtuvo '{fila_invitado[1]}'"
    assert fila_admin[1] != "Sistema" and bool(fila_admin[1]), f"Usuario para admin no debe ser 'Sistema' ni vacío, se obtuvo '{fila_admin[1]}'"
