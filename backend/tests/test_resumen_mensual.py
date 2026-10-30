import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.crypto import hash_password
from app.core.nit_utils import calcular_digito_verificador_nit
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Notificacion, ResultadoDimension
from app.models.organization import Organizacion
from app.models.survey import Dimension
from app.models.user import Rol, Usuario
from app.services.resumen_mensual import enviar_resumenes_mensuales

LOCAL = timezone(timedelta(hours=-5))
AHORA = datetime(2026, 11, 2, 9, 0, tzinfo=LOCAL)


@pytest.fixture(autouse=True)
def correos_enviados(monkeypatch):
    enviados = []

    def _mock_enviar(destino, asunto, contenido):
        enviados.append((destino, asunto, contenido))
        return True

    monkeypatch.setattr("app.services.resumen_mensual.enviar_correo", _mock_enviar)
    return enviados


def _crear_usuario(db_session, rol_codigo, organizacion_id=None, estado="ACTIVO", es_invitado=False):
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


def _crear_empresa(db_session, nombre=None, activa=True, creada_por=None):
    nit_base = str(uuid.uuid4().int)[:9]
    nit = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    creada_por_id = creada_por.id if hasattr(creada_por, "id") else creada_por
    org = Organizacion(
        nombre=nombre or f"Empresa {uuid.uuid4().hex[:6]}",
        nit=nit,
        activa=activa,
        creada_por_id=creada_por_id,
    )
    db_session.add(org)
    db_session.flush()
    return org


def _participante(
    db_session,
    crear_paciente,
    org,
    evaluador,
    fecha_fin,
    estado="COMPLETADA",
    estado_evaluacion="FINALIZADA",
):
    evaluacion = Evaluacion(
        organizacion_id=org.id,
        evaluador_id=evaluador.id,
        nombre=f"Eval {uuid.uuid4().hex[:6]}",
        estado=estado_evaluacion,
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


def test_envia_resumen_al_jefe_con_conteos(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)

    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 10, 10, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )
    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 10, 20, 15, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )
    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 9, 15, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )
    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=None,
        estado="PENDIENTE",
        estado_evaluacion="EN_CURSO",
    )

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 1
    asunto = jefe_correos[0][1]
    cuerpo = jefe_correos[0][2]

    assert "octubre de 2026" in asunto
    assert org.nombre in cuerpo
    assert "completados en el mes: 2" in cuerpo
    assert "3 de 4 asignados" in cuerpo
    assert "pendiente: 1" in cuerpo

    notis = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == jefe.id, Notificacion.tipo == "RESUMEN_MENSUAL")
        .all()
    )
    assert len(notis) == 1
    assert notis[0].titulo == "Resumen de octubre de 2026"


def test_con_menos_de_5_completados_no_muestra_dimensiones(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)

    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 10, 10, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )
    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 10, 20, 15, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )
    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 9, 15, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )
    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=None,
        estado="PENDIENTE",
        estado_evaluacion="EN_CURSO",
    )

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 1
    cuerpo = jefe_correos[0][2]
    assert "no se muestra para proteger el anonimato" in cuerpo
    assert "(acumulado): 0" not in cuerpo


def test_con_5_completados_muestra_dimensiones_alto_y_muy_alto(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)

    participantes = []
    for i in range(5):
        _, part = _participante(
            db_session,
            crear_paciente,
            org,
            psicologo,
            fecha_fin=datetime(2026, 10, 5 + i, 10, 0, tzinfo=LOCAL),
            estado="COMPLETADA",
        )
        participantes.append(part)

    dim = db_session.query(Dimension).first()
    assert dim is not None

    for part, nivel in zip(participantes[:3], ["ALTO", "ALTO", "MUY_ALTO"]):
        res = ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=25.0,
            puntaje_transformado=50.0,
            nivel=nivel,
        )
        db_session.add(res)
    db_session.flush()

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 1
    cuerpo = jefe_correos[0][2]
    assert "(acumulado): 3" in cuerpo


def test_el_correo_no_contiene_datos_personales(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)

    participantes = []
    pacientes_usuarios = []
    for i in range(5):
        evaluacion = Evaluacion(
            organizacion_id=org.id,
            evaluador_id=psicologo.id,
            nombre=f"Eval {uuid.uuid4().hex[:6]}",
            estado="FINALIZADA",
        )
        db_session.add(evaluacion)
        db_session.flush()

        paciente_info = crear_paciente(org.id)
        trabajador_id = paciente_info[0] if isinstance(paciente_info, tuple) else paciente_info.id
        u_paciente = db_session.query(Usuario).filter(Usuario.id == trabajador_id).first()
        pacientes_usuarios.append(u_paciente)

        part = EvaluacionParticipante(
            evaluacion_id=evaluacion.id,
            trabajador_id=trabajador_id,
            estado="COMPLETADA",
            fecha_fin=datetime(2026, 10, 5 + i, 10, 0, tzinfo=LOCAL),
        )
        db_session.add(part)
        db_session.flush()
        participantes.append(part)

    dim = db_session.query(Dimension).first()
    assert dim is not None

    for part, nivel in zip(participantes[:3], ["ALTO", "ALTO", "MUY_ALTO"]):
        res = ResultadoDimension(
            participante_id=part.id,
            dimension_id=dim.id,
            puntaje_bruto=25.0,
            puntaje_transformado=50.0,
            nivel=nivel,
        )
        db_session.add(res)
    db_session.flush()

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 1
    cuerpo = jefe_correos[0][2]

    assert psicologo.email not in cuerpo
    for p in pacientes_usuarios:
        assert p.email not in cuerpo
        assert p.nombre not in cuerpo


def test_es_idempotente(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)

    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 10, 10, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )

    enviar_resumenes_mensuales(db_session, ahora=AHORA)
    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 1

    notis = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == jefe.id, Notificacion.tipo == "RESUMEN_MENSUAL")
        .all()
    )
    assert len(notis) == 1


def test_solo_se_envia_en_los_primeros_dias_del_mes(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)

    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 10, 10, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )

    ahora_dia_10 = datetime(2026, 11, 10, 9, 0, tzinfo=LOCAL)
    enviar_resumenes_mensuales(db_session, ahora=ahora_dia_10)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 0

    notis = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == jefe.id, Notificacion.tipo == "RESUMEN_MENSUAL")
        .all()
    )
    assert len(notis) == 0


def test_empresa_sin_actividad_no_aparece(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org1 = _crear_empresa(db_session, nombre=f"Empresa Activa {uuid.uuid4().hex[:6]}", creada_por=jefe)
    org2 = _crear_empresa(db_session, nombre=f"Empresa Inactiva {uuid.uuid4().hex[:6]}", creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org1.id)

    _participante(
        db_session,
        crear_paciente,
        org1,
        psicologo,
        fecha_fin=datetime(2026, 10, 10, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 1
    cuerpo = jefe_correos[0][2]
    assert org1.nombre in cuerpo
    assert org2.nombre not in cuerpo


def test_sin_actividad_no_envia_correo_ni_notificacion(db_session, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    _crear_empresa(db_session, creada_por=jefe)

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 0

    notis = (
        db_session.query(Notificacion)
        .filter(Notificacion.usuario_id == jefe.id, Notificacion.tipo == "RESUMEN_MENSUAL")
        .all()
    )
    assert len(notis) == 0


def test_solo_reciben_jefe_administrador_y_responsable_activos(db_session, crear_paciente, correos_enviados):
    jefe_creador = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe_creador)
    responsable = _crear_usuario(db_session, "RESPONSABLE_SST", organizacion_id=org.id)

    evaluador = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)
    admin_otro = _crear_usuario(db_session, "ADMINISTRADOR")
    jefe_otro = _crear_usuario(db_session, "JEFE")

    jefe_inactivo = _crear_usuario(db_session, "JEFE", estado="INACTIVO")
    org_otra = _crear_empresa(db_session, creada_por=jefe_inactivo)
    _participante(
        db_session,
        crear_paciente,
        org_otra,
        evaluador,
        fecha_fin=datetime(2026, 10, 12, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )

    jefe_invitado = _crear_usuario(db_session, "JEFE", es_invitado=True)
    org_invitado = _crear_empresa(db_session, creada_por=jefe_invitado)
    _participante(
        db_session,
        crear_paciente,
        org_invitado,
        evaluador,
        fecha_fin=datetime(2026, 10, 14, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )

    evaluador_dueno = _crear_usuario(db_session, "EVALUADOR_SST")
    org_evaluador = _crear_empresa(db_session, creada_por=evaluador_dueno)
    _participante(
        db_session,
        crear_paciente,
        org_evaluador,
        evaluador,
        fecha_fin=datetime(2026, 10, 16, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )

    _participante(
        db_session,
        crear_paciente,
        org,
        evaluador,
        fecha_fin=datetime(2026, 10, 10, 10, 0, tzinfo=LOCAL),
        estado="COMPLETADA",
    )

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    destinatarios = [c[0] for c in correos_enviados]
    assert jefe_creador.email in destinatarios
    assert responsable.email in destinatarios
    assert evaluador.email not in destinatarios
    assert admin_otro.email not in destinatarios
    assert jefe_otro.email not in destinatarios
    assert jefe_inactivo.email not in destinatarios
    assert jefe_invitado.email not in destinatarios
    assert evaluador_dueno.email not in destinatarios


def test_los_limites_del_mes_usan_hora_de_colombia(db_session, crear_paciente, correos_enviados):
    jefe = _crear_usuario(db_session, "JEFE")
    org = _crear_empresa(db_session, creada_por=jefe)
    psicologo = _crear_usuario(db_session, "EVALUADOR_SST", organizacion_id=org.id)

    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 11, 1, 2, 0, tzinfo=timezone.utc),
        estado="COMPLETADA",
    )
    _participante(
        db_session,
        crear_paciente,
        org,
        psicologo,
        fecha_fin=datetime(2026, 10, 1, 3, 0, tzinfo=timezone.utc),
        estado="COMPLETADA",
    )

    enviar_resumenes_mensuales(db_session, ahora=AHORA)

    jefe_correos = [c for c in correos_enviados if c[0] == jefe.email]
    assert len(jefe_correos) == 1
    cuerpo = jefe_correos[0][2]
    assert "completados en el mes: 1" in cuerpo
