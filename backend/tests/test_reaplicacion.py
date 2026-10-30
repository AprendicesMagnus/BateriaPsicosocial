import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.crypto import hash_password
from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Notificacion
from app.models.organization import Organizacion
from app.models.user import Rol, Usuario
from app.services.reaplicacion import (
    TIPO_NOTIFICACION,
    TITULO_PROXIMO,
    TITULO_VENCIDO,
    enviar_recordatorios_reaplicacion,
)

REF = datetime(2025, 1, 10, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def mock_correo(monkeypatch):
    monkeypatch.setattr("app.services.reaplicacion.enviar_correo", lambda *args, **kwargs: True)


def _crear_empresa(db_session, nombre=None, activa=True):
    nit_base = str(uuid.uuid4().int)[:9]
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(
        nombre=nombre or f"Empresa {uuid.uuid4().hex[:6]}",
        nit=nit,
        activa=activa,
    )
    db_session.add(org)
    db_session.flush()
    return org


def _crear_usuario(db_session, rol_codigo, organizacion_id, estado="ACTIVO", es_invitado=False):
    rol = db_session.query(Rol).filter(Rol.codigo == rol_codigo).first()
    assert rol is not None, f"Rol {rol_codigo} no encontrado."
    email = f"{rol_codigo.lower()}_{uuid.uuid4().hex[:8]}@test.com"
    usuario = Usuario(
        nombre="Test",
        apellido="Usuario",
        email=email,
        password_hash=hash_password("Password1234"),
        rol_id=rol.id,
        organizacion_id=organizacion_id,
        estado=estado,
        es_invitado=es_invitado,
        email_verificado=True,
    )
    db_session.add(usuario)
    db_session.flush()
    return usuario


def _aplicacion_completada(db_session, crear_paciente, org, evaluador, fecha_fin, estado="COMPLETADA"):
    evaluacion = Evaluacion(
        organizacion_id=org.id,
        evaluador_id=evaluador.id,
        nombre=f"Eval {uuid.uuid4().hex[:6]}",
        estado="FINALIZADA",
    )
    db_session.add(evaluacion)
    db_session.flush()

    paciente = crear_paciente(org.id)
    trabajador_id = paciente[0] if isinstance(paciente, tuple) else paciente.id

    participante = EvaluacionParticipante(
        evaluacion_id=evaluacion.id,
        trabajador_id=trabajador_id,
        estado=estado,
        fecha_fin=fecha_fin,
    )
    db_session.add(participante)
    db_session.flush()
    return evaluacion, participante


def _notis(db_session, usuario):
    return (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id, Notificacion.tipo == TIPO_NOTIFICACION)
        .all()
    )


def test_sin_cuestionarios_completados_no_avisa(db_session, crear_paciente):
    org = _crear_empresa(db_session)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id)
    _aplicacion_completada(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=REF,
        estado="EN_CURSO",
    )
    ahora = REF + timedelta(days=400)
    enviar_recordatorios_reaplicacion(db_session, ahora=ahora)
    assert len(_notis(db_session, psicologo)) == 0


def test_antes_de_la_ventana_no_avisa(db_session, crear_paciente):
    org = _crear_empresa(db_session)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id)
    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=REF)
    ahora = REF + timedelta(days=300)
    enviar_recordatorios_reaplicacion(db_session, ahora=ahora)
    assert len(_notis(db_session, psicologo)) == 0


def test_dentro_de_30_dias_del_vencimiento_avisa_proximo(db_session, crear_paciente):
    org = _crear_empresa(db_session)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id)
    responsable = _crear_usuario(db_session, "RESPONSABLE_SST", org.id)
    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=REF)
    ahora = REF + timedelta(days=340)
    resultado = enviar_recordatorios_reaplicacion(db_session, ahora=ahora)

    notis_psicologo = _notis(db_session, psicologo)
    notis_responsable = _notis(db_session, responsable)

    assert len(notis_psicologo) == 1
    assert len(notis_responsable) == 1
    assert notis_psicologo[0].titulo == TITULO_PROXIMO
    assert notis_responsable[0].titulo == TITULO_PROXIMO
    assert org.nombre in notis_psicologo[0].mensaje
    assert "10/01/2025" in notis_psicologo[0].mensaje
    assert resultado["avisosEnviados"] >= 2


def test_vencido_avisa_con_titulo_de_vencimiento(db_session, crear_paciente):
    org = _crear_empresa(db_session)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id)
    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=REF)
    ahora = REF + timedelta(days=366)
    enviar_recordatorios_reaplicacion(db_session, ahora=ahora)

    notis = _notis(db_session, psicologo)
    assert len(notis) == 1
    assert notis[0].titulo == TITULO_VENCIDO
    mensaje_lower = notis[0].mensaje.lower()
    assert "riesgo" not in mensaje_lower
    assert "nivel" not in mensaje_lower


def test_es_idempotente_y_envia_cada_etapa_una_vez(db_session, crear_paciente):
    org = _crear_empresa(db_session)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id)
    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=REF)

    enviar_recordatorios_reaplicacion(db_session, ahora=REF + timedelta(days=340))
    enviar_recordatorios_reaplicacion(db_session, ahora=REF + timedelta(days=340))
    notis = _notis(db_session, psicologo)
    assert len(notis) == 1
    assert notis[0].titulo == TITULO_PROXIMO

    enviar_recordatorios_reaplicacion(db_session, ahora=REF + timedelta(days=366))
    enviar_recordatorios_reaplicacion(db_session, ahora=REF + timedelta(days=366))
    notis = _notis(db_session, psicologo)
    assert len(notis) == 2
    titulos = {n.titulo for n in notis}
    assert titulos == {TITULO_PROXIMO, TITULO_VENCIDO}


def test_nueva_aplicacion_reinicia_el_ciclo(db_session, crear_paciente):
    org = _crear_empresa(db_session)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id)
    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=REF)

    enviar_recordatorios_reaplicacion(db_session, ahora=REF + timedelta(days=366))
    assert len(_notis(db_session, psicologo)) == 1

    nueva_fecha = REF + timedelta(days=400)
    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=nueva_fecha)

    enviar_recordatorios_reaplicacion(db_session, ahora=REF + timedelta(days=410))
    assert len(_notis(db_session, psicologo)) == 1

    ahora_nuevo_vencido = nueva_fecha + timedelta(days=366)
    enviar_recordatorios_reaplicacion(db_session, ahora=ahora_nuevo_vencido)

    notis = _notis(db_session, psicologo)
    vencidos = [n for n in notis if n.titulo == TITULO_VENCIDO]
    assert len(vencidos) == 2
    assert len(notis) == 2
    nueva_fecha_str = f"{nueva_fecha:%d/%m/%Y}"
    assert any(nueva_fecha_str in n.mensaje for n in vencidos)


def test_solo_avisa_a_psicologo_y_responsable_activos(db_session, crear_paciente):
    org = _crear_empresa(db_session)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id, estado="ACTIVO")
    responsable = _crear_usuario(db_session, "RESPONSABLE_SST", org.id, estado="ACTIVO")
    jefe = _crear_usuario(db_session, "JEFE", org.id, estado="ACTIVO")
    admin = _crear_usuario(db_session, "ADMINISTRADOR", org.id, estado="ACTIVO")
    evaluador_inactivo = _crear_usuario(db_session, "EVALUADOR_SST", org.id, estado="INACTIVO")
    invitado = _crear_usuario(db_session, "EVALUADOR_SST", org.id, estado="ACTIVO", es_invitado=True)

    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=REF)
    ahora = REF + timedelta(days=366)
    enviar_recordatorios_reaplicacion(db_session, ahora=ahora)

    assert len(_notis(db_session, psicologo)) == 1
    assert len(_notis(db_session, responsable)) == 1
    assert len(_notis(db_session, jefe)) == 0
    assert len(_notis(db_session, admin)) == 0
    assert len(_notis(db_session, evaluador_inactivo)) == 0
    assert len(_notis(db_session, invitado)) == 0


def test_empresa_inactiva_no_recibe_avisos(db_session, crear_paciente):
    org = _crear_empresa(db_session, activa=False)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", org.id)
    _aplicacion_completada(db_session, crear_paciente, org, psicologo, fecha_fin=REF)
    ahora = REF + timedelta(days=366)
    enviar_recordatorios_reaplicacion(db_session, ahora=ahora)
    assert len(_notis(db_session, psicologo)) == 0
