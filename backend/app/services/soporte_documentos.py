import re
import unicodedata
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, undefer

from app.core.errors import AppError
from app.models.soporte_documento import SoporteDocumento

MAX_DOCUMENTO_BYTES = 10 * 1024 * 1024  # 10 MB

_OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # formato binario antiguo de Office (.doc, .xls, .ppt)
_ZIP = b"PK\x03\x04"  # formato moderno de Office (.docx, .xlsx, .pptx)

# extensión -> (tipo MIME con el que se sirve, firma esperada al inicio del archivo)
TIPOS_PERMITIDOS: dict[str, tuple[str, bytes]] = {
    "pdf": ("application/pdf", b"%PDF-"),
    "doc": ("application/msword", _OLE),
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", _ZIP),
    "xls": ("application/vnd.ms-excel", _OLE),
    "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", _ZIP),
    "ppt": ("application/vnd.ms-powerpoint", _OLE),
    "pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", _ZIP),
}


def _meta(d: SoporteDocumento) -> dict:
    return {
        "id": str(d.id),
        "titulo": d.titulo,
        "descripcion": d.descripcion,
        "nombreArchivo": d.nombre_archivo,
        "extension": d.nombre_archivo.rsplit(".", 1)[-1].lower() if "." in d.nombre_archivo else "",
        "tamano": d.tamano,
        "orden": d.orden,
        "activo": d.activo,
        "creadoEn": d.creado_en.isoformat() if d.creado_en else None,
    }


def _nombre_seguro(nombre: str) -> str:
    """Quita rutas y caracteres raros del nombre que envía el navegador."""
    base = (nombre or "").replace("\\", "/").split("/")[-1].strip()
    base = unicodedata.normalize("NFC", base)
    base = re.sub(r"[^\w.\- ()]", "_", base, flags=re.UNICODE)
    return base[:200] or "documento"


def validar_archivo(nombre: str, contenido: bytes) -> tuple[str, str]:
    """Devuelve (nombre seguro, tipo MIME) o lanza AppError si el archivo no es válido."""
    nombre = _nombre_seguro(nombre)
    ext = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
    if ext not in TIPOS_PERMITIDOS:
        raise AppError(400, "Formato no permitido. Sube un PDF, Word, Excel o PowerPoint.")
    if not contenido:
        raise AppError(400, "El archivo está vacío.")
    if len(contenido) > MAX_DOCUMENTO_BYTES:
        raise AppError(400, "El archivo supera el máximo de 10 MB.")
    mime, firma = TIPOS_PERMITIDOS[ext]
    if not contenido.startswith(firma):
        raise AppError(400, f"El archivo no es un .{ext} válido.")
    return nombre, mime


def listar_publico(db: Session) -> list[dict]:
    filas = (
        db.query(SoporteDocumento)
        .filter(SoporteDocumento.activo.is_(True))
        .order_by(SoporteDocumento.orden.asc(), SoporteDocumento.creado_en.asc())
        .all()
    )
    return [_meta(d) for d in filas]


def listar_admin(db: Session) -> list[dict]:
    filas = db.query(SoporteDocumento).order_by(SoporteDocumento.orden.asc(), SoporteDocumento.creado_en.asc()).all()
    return [_meta(d) for d in filas]


def crear(db: Session, *, nombre: str, contenido: bytes, titulo: str, descripcion: str | None, activo: bool, usuario_id) -> dict:
    titulo = (titulo or "").strip()
    if not titulo:
        raise AppError(400, "Escribe el título del documento.")
    if len(titulo) > 200:
        raise AppError(400, "El título no puede superar 200 caracteres.")
    descripcion = (descripcion or "").strip() or None
    if descripcion and len(descripcion) > 500:
        raise AppError(400, "La descripción no puede superar 500 caracteres.")
    nombre, mime = validar_archivo(nombre, contenido)
    maximo = db.query(func.max(SoporteDocumento.orden)).scalar()
    doc = SoporteDocumento(
        titulo=titulo,
        descripcion=descripcion,
        nombre_archivo=nombre,
        tipo_mime=mime,
        tamano=len(contenido),
        contenido=contenido,
        orden=(maximo or 0) + 1,
        activo=activo,
        creado_por=usuario_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _meta(doc)


def _obtener(db: Session, doc_id: UUID) -> SoporteDocumento:
    doc = db.get(SoporteDocumento, doc_id)
    if not doc:
        raise AppError(404, "No se encontró el documento.")
    return doc


def actualizar(db: Session, doc_id: UUID, data) -> dict:
    doc = _obtener(db, doc_id)
    cambios = data.model_dump(exclude_unset=True)
    if "titulo" in cambios:
        titulo = (cambios["titulo"] or "").strip()
        if not titulo:
            raise AppError(400, "Escribe el título del documento.")
        doc.titulo = titulo
    if "descripcion" in cambios:
        doc.descripcion = (cambios["descripcion"] or "").strip() or None
    if "orden" in cambios and cambios["orden"] is not None:
        doc.orden = cambios["orden"]
    if "activo" in cambios and cambios["activo"] is not None:
        doc.activo = cambios["activo"]
    db.commit()
    db.refresh(doc)
    return _meta(doc)


def eliminar(db: Session, doc_id: UUID) -> dict:
    doc = _obtener(db, doc_id)
    db.delete(doc)
    db.commit()
    return {"ok": True}


def obtener_para_descarga(db: Session, doc_id: UUID, *, es_admin: bool) -> SoporteDocumento:
    doc = db.query(SoporteDocumento).options(undefer(SoporteDocumento.contenido)).filter(SoporteDocumento.id == doc_id).first()
    if not doc or (not doc.activo and not es_admin):
        raise AppError(404, "No se encontró el documento.")
    return doc
