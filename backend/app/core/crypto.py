import re
from datetime import datetime, timezone

import bcrypt

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def password_valida(password: str) -> bool:
    return bool(PASSWORD_REGEX.match(password or ""))


def email_valido(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email or ""))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
