from datetime import timedelta
from sqlalchemy.orm import Session, joinedload

from app.core.roles import ROLES_EVALUADOR
from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Notificacion
from app.models.user import Usuario
from app.services.correo import enviar_correo


def notificar(
    db: Session,
    *,
    usuario_id,
    tipo: str,
    titulo: str,
    mensaje: str,
    evaluacion_id=None,
    commit: bool = True,
) -> Notificacion:
    registro = Notificacion(
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        evaluacion_id=evaluacion_id,
        fecha_envio=utcnow(),
    )
    db.add(registro)
    if commit:
        db.commit()
        db.refresh(registro)
    return registro


def listar_notificaciones(db: Session, usuario_id) -> list[dict]:
    registros = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario_id)
        .order_by(Notificacion.fecha_envio.desc())
        .all()
    )
    return [
        {
            "id": str(n.id),
            "tipo": n.tipo,
            "titulo": n.titulo,
            "mensaje": n.mensaje,
            "leida": n.leida,
            "evaluacionId": str(n.evaluacion_id) if n.evaluacion_id else None,
            "fechaEnvio": n.fecha_envio.isoformat(),
            "fechaLectura": n.fecha_lectura.isoformat() if n.fecha_lectura else None,
        }
        for n in registros
    ]


def marcar_leida(db: Session, notificacion_id, usuario_id) -> dict:
    registro = (
        db.query(Notificacion)
        .filter(Notificacion.id == notificacion_id, Notificacion.usuario_id == usuario_id)
        .first()
    )
    if registro is None:
        return {"message": "Notificación no encontrada."}
    if not registro.leida:
        registro.leida = True
        registro.fecha_lectura = utcnow()
        db.commit()
    return {"message": "Notificación marcada como leída."}


def _ejecutar_envio_recordatorios(db: Session, horas_idempotencia: int = 24) -> dict:
    """Lógica de sistema para enviar recordatorios pendientes, sin validación de rol.
    Puede ser invocada por el scheduler automatico o por enviar_recordatorios_pendientes."""

    query = (
        db.query(EvaluacionParticipante)
        .join(EvaluacionParticipante.evaluacion)
        .join(EvaluacionParticipante.trabajador)
        .options(
            joinedload(EvaluacionParticipante.evaluacion),
            joinedload(EvaluacionParticipante.trabajador),
        )
        .filter(
            Evaluacion.estado == "EN_CURSO",
            EvaluacionParticipante.estado != "COMPLETADA",
        )
    )

    participantes_pendientes = query.all()

    ahora = utcnow()
    limite_idempotencia = ahora - timedelta(hours=horas_idempotencia)

    enviados_count = 0
    omitidos_count = 0
    detalles = []

    for part in participantes_pendientes:
        # Criterio de idempotencia: Verificar si ya se envió un recordatorio en las últimas N horas
        existente = (
            db.query(Notificacion)
            .filter(
                Notificacion.usuario_id == part.trabajador_id,
                Notificacion.evaluacion_id == part.evaluacion_id,
                Notificacion.tipo == "RECORDATORIO_EVALUACION",
                Notificacion.fecha_envio >= limite_idempotencia,
            )
            .first()
        )

        if existente:
            omitidos_count += 1
            detalles.append({
                "trabajadorId": str(part.trabajador_id),
                "email": part.trabajador.email,
                "evaluacionId": str(part.evaluacion_id),
                "estadoNotificacion": "OMITIDA_RECIENTE",
            })
            continue

        titulo = "Recordatorio: Evaluación Psicosocial Pendiente"
        mensaje_texto = (
            f"Hola {part.trabajador.nombre}, tienes instrumentos pendientes por completar en la "
            f"evaluación '{part.evaluacion.nombre}'. Por favor ingresa al sistema para completarlos."
        )

        noti = Notificacion(
            usuario_id=part.trabajador_id,
            tipo="RECORDATORIO_EVALUACION",
            titulo=titulo,
            mensaje=mensaje_texto,
            evaluacion_id=part.evaluacion_id,
            fecha_envio=ahora,
        )
        db.add(noti)

        # Intento de envío de correo electrónico seguro (no detiene el flujo si falla SMTP)
        enviar_correo(part.trabajador.email, titulo, mensaje_texto)

        enviados_count += 1
        detalles.append({
            "trabajadorId": str(part.trabajador_id),
            "email": part.trabajador.email,
            "evaluacionId": str(part.evaluacion_id),
            "estadoNotificacion": "ENVIADA",
        })

    db.commit()

    return {
        "message": f"Proceso finalizado. Recordatorios enviados: {enviados_count}, omitidos por idempotencia: {omitidos_count}.",
        "enviadosCount": enviados_count,
        "omitidosCount": omitidos_count,
        "detalles": detalles,
    }


def enviar_recordatorios_pendientes(
    db: Session, actual: Usuario, horas_idempotencia: int = 24
) -> dict:
    if actual.rol.codigo not in {"SUPER_ADMINISTRADOR", *ROLES_EVALUADOR}:
        raise AppError(403, "No tiene permisos para enviar recordatorios de evaluación.")

    # Si es EVALUADOR_SST, la query interna no filtra por evaluador — el endpoint original tampoco
    # ofrecía ese filtro al llamar la lógica; se mantiene comportamiento compatible.
    return _ejecutar_envio_recordatorios(db, horas_idempotencia)
