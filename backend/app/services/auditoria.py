from fastapi import Request
from sqlalchemy.orm import Session

from app.core.crypto import utcnow
from app.models.audit import Auditoria
from app.models.user import Usuario


def registrar_auditoria(
    db: Session,
    *,
    usuario: Usuario | None,
    accion: str,
    entidad: str | None = None,
    entidad_id: str | None = None,
    request: Request | None = None,
    detalle: dict | None = None,
) -> None:
    ip = None
    if request is not None:
        ip = request.client.host if request.client else None
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
    registro = Auditoria(
        usuario_id=usuario.id if usuario else None,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        ip_origen=ip,
        detalle=detalle,
        registrado_en=utcnow(),
    )
    db.add(registro)
    db.commit()


def listar_auditoria(db: Session, limite: int = 200) -> list[dict]:
    registros = db.query(Auditoria).order_by(Auditoria.registrado_en.desc()).limit(limite).all()
    return [
        {
            "id": str(a.id),
            "usuarioId": str(a.usuario_id) if a.usuario_id else None,
            "accion": a.accion,
            "entidad": a.entidad,
            "entidadId": a.entidad_id,
            "ipOrigen": a.ip_origen,
            "detalle": a.detalle,
            "registradoEn": a.registrado_en.isoformat(),
        }
        for a in registros
    ]
