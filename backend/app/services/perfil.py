"""Edición de perfil del propio usuario y directorio de usuarios (solo Super Administrador).

Reglas de negocio:
- Nombres, apellidos, contraseña y foto se pueden editar UNA vez cada 15 días.
  La fecha de la última edición se guarda en usuarios.perfil_actualizado_en.
- El SUPER_ADMINISTRADOR está exento de esa restricción.
- El cambio de contraseña desde el perfil es independiente del flujo "Olvidé mi contraseña":
  no toca codigos_verificacion ni tokens de restablecimiento.
"""
import io
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.crypto import hash_password, password_valida, utcnow, verificar_password
from app.core.errors import AppError
from app.models.user import Rol, Usuario
from app.schemas.common import PATRON_NOMBRE_PERSONA

DIAS_ENTRE_EDICIONES = 15
MAX_FOTO_BYTES = 2 * 1024 * 1024  # 2 MB
FORMATOS_FOTO = {"JPEG", "PNG", "WEBP"}
LADO_MAXIMO_FOTO = 512
Image.MAX_IMAGE_PIXELS = 25_000_000  # protección contra "decompression bombs"

UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
AVATARS_DIR = UPLOADS_DIR / "avatars"
URL_AVATARS = "/api/uploads/avatars"


def es_super_admin(usuario: Usuario) -> bool:
    return usuario.rol.codigo == "SUPER_ADMINISTRADOR"


def proxima_edicion(usuario: Usuario) -> datetime | None:
    """Fecha desde la cual puede volver a editar; None si puede editar ya."""
    if es_super_admin(usuario) or usuario.perfil_actualizado_en is None:
        return None
    desbloqueo = usuario.perfil_actualizado_en + timedelta(days=DIAS_ENTRE_EDICIONES)
    return desbloqueo if desbloqueo > utcnow() else None


def _asegurar_puede_editar(usuario: Usuario) -> None:
    desbloqueo = proxima_edicion(usuario)
    if desbloqueo is not None:
        raise AppError(
            403,
            "Solo puedes editar tu perfil cada 15 días. "
            f"Podrás hacerlo de nuevo el {desbloqueo.strftime('%d/%m/%Y')}.",
        )


def _validar_nombre(valor: str, etiqueta: str) -> str:
    limpio = re.sub(r"\s+", " ", valor).strip()
    if len(limpio) < 2 or len(limpio) > 100 or not re.match(PATRON_NOMBRE_PERSONA, limpio):
        raise AppError(400, f"{etiqueta} solo puede contener letras y espacios (2 a 100 caracteres).")
    return limpio


def _procesar_foto(contenido: bytes) -> bytes:
    if len(contenido) > MAX_FOTO_BYTES:
        raise AppError(400, "La foto no puede superar los 2 MB.")
    try:
        with Image.open(io.BytesIO(contenido)) as img:
            if img.format not in FORMATOS_FOTO:
                raise AppError(400, "Formato de imagen no permitido. Usa JPG, PNG o WEBP.")
            img = ImageOps.exif_transpose(img).convert("RGB")
            img = ImageOps.fit(img, (LADO_MAXIMO_FOTO, LADO_MAXIMO_FOTO), method=Image.Resampling.LANCZOS)
            salida = io.BytesIO()
            img.save(salida, format="JPEG", quality=85)
            return salida.getvalue()
    except AppError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise AppError(400, "El archivo no es una imagen válida.")


def _guardar_foto(usuario: Usuario, contenido: bytes) -> str:
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"{usuario.id}-{uuid.uuid4().hex[:8]}.jpg"
    (AVATARS_DIR / nombre).write_bytes(_procesar_foto(contenido))
    return f"{URL_AVATARS}/{nombre}"


def _borrar_foto_anterior(url: str | None) -> None:
    if url and url.startswith(URL_AVATARS + "/"):
        ruta = AVATARS_DIR / Path(url).name
        if ruta.is_file():
            ruta.unlink(missing_ok=True)


def editar_perfil(
    db: Session,
    usuario: Usuario,
    *,
    nombre: str | None,
    apellido: str | None,
    foto: bytes | None,
) -> Usuario:
    if nombre is None and apellido is None and foto is None:
        raise AppError(400, "No enviaste ningún cambio.")
    _asegurar_puede_editar(usuario)

    nuevo_nombre = _validar_nombre(nombre, "El nombre") if nombre is not None else None
    nuevo_apellido = _validar_nombre(apellido, "El apellido") if apellido is not None else None
    nueva_foto = _guardar_foto(usuario, foto) if foto is not None else None

    foto_anterior = usuario.foto_url
    if nuevo_nombre is not None:
        usuario.nombre = nuevo_nombre
    if nuevo_apellido is not None:
        usuario.apellido = nuevo_apellido
    if nueva_foto is not None:
        usuario.foto_url = nueva_foto
    usuario.perfil_actualizado_en = utcnow()
    db.commit()
    db.refresh(usuario)

    if nueva_foto is not None:
        _borrar_foto_anterior(foto_anterior)
    return usuario


def cambiar_password(db: Session, usuario: Usuario, password_actual: str, password_nueva: str) -> Usuario:
    _asegurar_puede_editar(usuario)
    if not verificar_password(password_actual, usuario.password_hash):
        # 400 (no 401) para que el frontend no interprete la respuesta como sesión vencida.
        raise AppError(400, "La contraseña actual no es correcta.")
    if password_actual == password_nueva:
        raise AppError(400, "La nueva contraseña debe ser distinta de la actual.")
    if not password_valida(password_nueva):
        raise AppError(
            400, "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números."
        )
    usuario.password_hash = hash_password(password_nueva)
    usuario.perfil_actualizado_en = utcnow()
    db.commit()
    db.refresh(usuario)
    return usuario


def listar_directorio(db: Session, q: str | None, limite: int, desplazamiento: int) -> dict:
    """Todos los usuarios, exponiendo SOLO nombre completo, correo y rol."""
    query = db.query(Usuario).options(joinedload(Usuario.rol)).join(Rol, Rol.id == Usuario.rol_id)
    if q:
        patron = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Usuario.nombre.ilike(patron),
                Usuario.apellido.ilike(patron),
                Usuario.email.ilike(patron),
                func.concat(Usuario.nombre, " ", Usuario.apellido).ilike(patron),
            )
        )
    total = query.count()
    usuarios = query.order_by(Usuario.nombre.asc(), Usuario.apellido.asc()).limit(limite).offset(desplazamiento).all()
    return {
        "total": total,
        "items": [
            {
                "nombreCompleto": f"{u.nombre} {u.apellido}".strip(),
                "email": u.email,
                "rol": u.rol.codigo,
            }
            for u in usuarios
        ],
    }