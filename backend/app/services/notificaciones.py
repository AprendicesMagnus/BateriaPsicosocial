from sqlalchemy.orm import Session

from app.core.crypto import utcnow
from app.models.evaluation import Notificacion


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
