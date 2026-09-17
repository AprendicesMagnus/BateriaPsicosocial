import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    if not settings.encryption_key or not settings.encryption_key.strip():
        raise RuntimeError(
            "ENCRYPTION_KEY no está configurada en las variables de entorno (.env). "
            "Por seguridad de los datos psicosociales, defina una clave Fernet válida de 44 caracteres."
        )
    raw = settings.encryption_key.encode("utf-8")
    if len(raw) == 44:
        return Fernet(raw)
    digest = hashlib.sha256(raw).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def cifrar_json(valor: Any) -> str:
    payload = json.dumps(valor, ensure_ascii=False).encode("utf-8")
    return _fernet().encrypt(payload).decode("utf-8")


def descifrar_json(token: str) -> Any:
    try:
        data = _fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("No fue posible descifrar el valor almacenado.") from exc
    return json.loads(data.decode("utf-8"))
