from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.soporte_item import SoporteItem


def _publico(i: SoporteItem) -> dict:
    return {"id": str(i.id), "seccion": i.seccion, "titulo": i.titulo, "texto": i.texto, "orden": i.orden, "activo": i.activo}


def contenido_publico(db: Session) -> dict:
    """Lo que ve cualquier usuario: solo los elementos visibles, agrupados por sección."""
    items = db.query(SoporteItem).filter(SoporteItem.activo.is_(True)).order_by(SoporteItem.orden.asc()).all()
    salida: dict[str, list] = {}
    for i in items:
        salida.setdefault(i.seccion, []).append(_publico(i))
    return salida


def listar_admin(db: Session) -> list[dict]:
    items = db.query(SoporteItem).order_by(SoporteItem.seccion.asc(), SoporteItem.orden.asc()).all()
    return [_publico(i) for i in items]


def crear_item(db: Session, data) -> dict:
    orden = data.orden
    if orden is None:
        maximo = db.query(func.max(SoporteItem.orden)).filter(SoporteItem.seccion == data.seccion).scalar()
        orden = (maximo or 0) + 1
    item = SoporteItem(
        seccion=data.seccion,
        titulo=(data.titulo or "").strip() or None,
        texto=data.texto.strip(),
        orden=orden,
        activo=data.activo,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _publico(item)


def _obtener(db: Session, item_id) -> SoporteItem:
    item = db.query(SoporteItem).filter(SoporteItem.id == item_id).first()
    if item is None:
        raise AppError(404, "Elemento no encontrado.")
    return item


def actualizar_item(db: Session, item_id, data) -> dict:
    item = _obtener(db, item_id)
    cambios = data.model_dump(exclude_unset=True)
    if "titulo" in cambios:
        item.titulo = (cambios["titulo"] or "").strip() or None
    if cambios.get("texto") is not None:
        item.texto = cambios["texto"].strip()
    if cambios.get("orden") is not None:
        item.orden = cambios["orden"]
    if cambios.get("activo") is not None:
        item.activo = cambios["activo"]
    db.commit()
    db.refresh(item)
    return _publico(item)


def eliminar_item(db: Session, item_id) -> dict:
    db.delete(_obtener(db, item_id))
    db.commit()
    return {"message": "Elemento eliminado."}
