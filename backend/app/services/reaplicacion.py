"""Recordatorio de reaplicacion de la bateria de riesgo psicosocial.

Criterio de diseño: la plataforma recomienda volver a aplicar la bateria cada 12 meses, contados
desde el ultimo cuestionario completado en la empresa, sin calcular el nivel de riesgo. Es el plazo
mas exigente de la Resolucion 2764 de 2022 (art. 3: anual con riesgo alto; cada dos años con riesgo
medio o bajo). El aviso es una recomendacion, no una constancia de cumplimiento normativo.
"""

from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.crypto import utcnow
from app.core.roles import ROLES_EVALUADOR
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Notificacion
from app.models.organization import Organizacion
from app.models.user import Rol, Usuario
from app.services.correo import enviar_correo
from app.services.notificaciones import notificar

TIPO_NOTIFICACION = "RECORDATORIO_REAPLICACION"
PLAZO_REAPLICACION_DIAS = 365
ANTELACION_AVISO_DIAS = 30
TITULO_PROXIMO = "Se acerca la fecha para volver a evaluar"
TITULO_VENCIDO = "Llegó la fecha para volver a evaluar"


def _ultima_aplicacion(db: Session, organizacion_id) -> datetime | None:
    """Fecha del ultimo cuestionario completado en la empresa (None si no hay ninguno)."""
    return (
        db.query(func.max(EvaluacionParticipante.fecha_fin))
        .join(Evaluacion, Evaluacion.id == EvaluacionParticipante.evaluacion_id)
        .filter(
            Evaluacion.organizacion_id == organizacion_id,
            EvaluacionParticipante.estado == "COMPLETADA",
            EvaluacionParticipante.fecha_fin.is_not(None),
        )
        .scalar()
    )


def _destinatarios(db: Session, organizacion_id) -> list[Usuario]:
    """Psicologo y Responsable SST activos de la empresa (vinculados a ella o que la han evaluado)."""
    evaluadores = select(Evaluacion.evaluador_id).where(Evaluacion.organizacion_id == organizacion_id)
    return (
        db.query(Usuario)
        .filter(
            Usuario.estado == "ACTIVO",
            Usuario.es_invitado.is_(False),
            Usuario.rol.has(Rol.codigo.in_(sorted(ROLES_EVALUADOR))),
            or_(Usuario.organizacion_id == organizacion_id, Usuario.id.in_(evaluadores)),
        )
        .all()
    )


def _textos(nombre_empresa: str, referencia: datetime, vence: datetime, vencido: bool) -> tuple[str, str]:
    fecha_referencia = f"{referencia:%d/%m/%Y}"
    if vencido:
        return (
            TITULO_VENCIDO,
            f"Han pasado 12 meses desde la última aplicación de la batería en {nombre_empresa} "
            f"(el {fecha_referencia}). Se recomienda volver a aplicarla.",
        )
    return (
        TITULO_PROXIMO,
        f"La última aplicación de la batería en {nombre_empresa} fue el {fecha_referencia}. "
        f"Se recomienda volver a aplicarla antes del {vence:%d/%m/%Y}.",
    )


def enviar_recordatorios_reaplicacion(db: Session, ahora: datetime | None = None) -> dict:
    """Avisa por la campana y por correo a quienes gestionan una empresa cuando se acerca o llego
    la fecha de volver a aplicar la bateria. Es idempotente: cada aviso se envia una sola vez por
    usuario y por ultima aplicacion (la fecha de referencia forma parte del mensaje)."""
    ahora = ahora or utcnow()
    organizaciones = db.query(Organizacion).filter(Organizacion.activa.is_(True)).all()
    avisos = 0

    for organizacion in organizaciones:
        referencia = _ultima_aplicacion(db, organizacion.id)
        if referencia is None:
            continue
        vence = referencia + timedelta(days=PLAZO_REAPLICACION_DIAS)
        if ahora >= vence:
            vencido = True
        elif ahora >= vence - timedelta(days=ANTELACION_AVISO_DIAS):
            vencido = False
        else:
            continue

        titulo, mensaje = _textos(organizacion.nombre, referencia, vence, vencido)
        marca_ciclo = f"{referencia:%d/%m/%Y}"
        for usuario in _destinatarios(db, organizacion.id):
            ya_enviado = (
                db.query(Notificacion.id)
                .filter(
                    Notificacion.usuario_id == usuario.id,
                    Notificacion.tipo == TIPO_NOTIFICACION,
                    Notificacion.titulo == titulo,
                    Notificacion.mensaje.contains(marca_ciclo),
                )
                .first()
            )
            if ya_enviado:
                continue
            notificar(
                db,
                usuario_id=usuario.id,
                tipo=TIPO_NOTIFICACION,
                titulo=titulo,
                mensaje=mensaje,
                commit=False,
            )
            enviar_correo(usuario.email, titulo, mensaje)
            avisos += 1

    db.commit()
    return {"empresasRevisadas": len(organizaciones), "avisosEnviados": avisos}
