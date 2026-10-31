import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import utcnow
from app.core.security import crear_token_sesion
from app.models.security import DispositivoConfiable, SesionActiva
from app.models.user import Usuario

settings = get_settings()
HORAS_DISPOSITIVO_CONFIABLE = 4


def _sha256(valor: str) -> str:
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()


def dispositivo_desde_request(request) -> str:
    agente = (request.headers.get("user-agent") or "Dispositivo desconocido").strip()
    return agente[:255]


def crear_sesion(db: Session, usuario: Usuario, request, dispositivo_confiable: str | None = None) -> dict:
    ahora = utcnow()
    session_id = secrets.token_urlsafe(24)
    expiracion = ahora + timedelta(minutes=settings.jwt_expira_minutos)
    sesion = SesionActiva(
        usuario_id=usuario.id,
        token_id=session_id,
        dispositivo=dispositivo_desde_request(request),
        ip=request.client.host if request.client else None,
        creado_en=ahora,
        ultimo_acceso=ahora,
        expiracion=expiracion,
        revocada=False,
    )
    db.add(sesion)
    token = crear_token_sesion(str(usuario.id), usuario.rol.codigo, usuario.email, session_id)

    resultado = {"token": token, "usuario": None}
    if dispositivo_confiable:
        resultado["trustedDeviceToken"] = dispositivo_confiable
    return resultado


def dispositivo_es_confiable(db: Session, usuario: Usuario, token: str | None, request) -> bool:
    if not token or len(token) > 512:
        return False
    registro = (
        db.query(DispositivoConfiable)
        .filter(
            DispositivoConfiable.usuario_id == usuario.id,
            DispositivoConfiable.token_hash == _sha256(token),
            DispositivoConfiable.revocado.is_(False),
            DispositivoConfiable.expira_en > utcnow(),
        )
        .first()
    )
    return registro is not None and secrets.compare_digest(registro.nombre, dispositivo_desde_request(request))


def crear_dispositivo_confiable(db: Session, usuario: Usuario, request) -> str:
    token = secrets.token_urlsafe(48)
    ahora = utcnow()
    db.add(DispositivoConfiable(
        usuario_id=usuario.id,
        token_hash=_sha256(token),
        nombre=dispositivo_desde_request(request),
        creado_en=ahora,
        expira_en=ahora + timedelta(hours=HORAS_DISPOSITIVO_CONFIABLE),
        revocado=False,
    ))
    return token


def listar_sesiones(db: Session, usuario: Usuario, token_id: str | None) -> list[dict]:
    ahora = utcnow()
    filas = (
        db.query(SesionActiva)
        .filter(
            SesionActiva.usuario_id == usuario.id,
            SesionActiva.revocada.is_(False),
            SesionActiva.expiracion > ahora,
        )
        .order_by(SesionActiva.ultimo_acceso.desc())
        .all()
    )
    return [{
        "id": str(fila.id),
        "dispositivo": fila.dispositivo,
        "ip": fila.ip,
        "creadoEn": fila.creado_en.isoformat(),
        "ultimoAcceso": fila.ultimo_acceso.isoformat(),
        "expiracion": fila.expiracion.isoformat(),
        "actual": fila.token_id == token_id,
    } for fila in filas]


def cerrar_sesion(db: Session, usuario: Usuario, session_id: UUID, token_id: str | None) -> None:
    fila = db.query(SesionActiva).filter(
        SesionActiva.id == session_id,
        SesionActiva.usuario_id == usuario.id,
        SesionActiva.revocada.is_(False),
    ).first()
    if fila:
        fila.revocada = True
        if fila.token_id == token_id:
            # El frontend elimina el JWT después de recibir esta respuesta.
            pass
        db.commit()


def cerrar_otras_sesiones(db: Session, usuario: Usuario, token_id: str | None) -> int:
    filas = db.query(SesionActiva).filter(
        SesionActiva.usuario_id == usuario.id,
        SesionActiva.revocada.is_(False),
        SesionActiva.token_id != (token_id or ""),
    ).all()
    for fila in filas:
        fila.revocada = True
    db.commit()
    return len(filas)


def revocar_sesion_actual(db: Session, usuario: Usuario, token_id: str | None) -> None:
    if not token_id:
        return
    fila = db.query(SesionActiva).filter(
        SesionActiva.usuario_id == usuario.id,
        SesionActiva.token_id == token_id,
        SesionActiva.revocada.is_(False),
    ).first()
    if fila:
        fila.revocada = True
        db.commit()


def revocar_dispositivos_confianza(db: Session, usuario: Usuario) -> int:
    filas = db.query(DispositivoConfiable).filter(
        DispositivoConfiable.usuario_id == usuario.id,
        DispositivoConfiable.revocado.is_(False),
    ).all()
    for fila in filas:
        fila.revocado = True
    db.commit()
    return len(filas)
