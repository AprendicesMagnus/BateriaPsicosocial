from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings
from app.core.errors import AppError

settings = get_settings()
ALGORITMO = "HS256"


def crear_token(datos: dict[str, Any], minutos: int) -> str:
    payload = dict(datos)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=minutos)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITMO)


def crear_token_sesion(usuario_id: str, rol: str, email: str) -> str:
    return crear_token(
        {"sub": usuario_id, "rol": rol, "email": email},
        settings.jwt_expira_minutos,
    )


def crear_token_reset(usuario_id: str) -> str:
    return crear_token(
        {"sub": usuario_id, "purpose": "reset_password"},
        settings.reset_expira_minutos,
    )


def decodificar_token(token: str, *, error_sesion: bool = True) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITMO])
    except JWTError as exc:
        mensaje = "Sesión inválida o expirada." if error_sesion else "El enlace de restablecimiento es inválido o expiró."
        codigo = 401 if error_sesion else 400
        raise AppError(codigo, mensaje) from exc
