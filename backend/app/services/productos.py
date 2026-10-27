from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.product import Producto


CATEGORIAS = {"SST", "Tecnología"}


def _publico(producto: Producto) -> dict:
    return {
        "id": str(producto.id),
        "nombre": producto.nombre,
        "categoria": producto.categoria,
        "precio": producto.precio,
        "imagen_url": producto.imagen_url,
        "activo": producto.activo,
    }


def listar_productos(db: Session, solo_activos: bool = True) -> list[dict]:
    query = db.query(Producto)
    if solo_activos:
        query = query.filter(Producto.activo.is_(True))
    productos = query.order_by(Producto.categoria.asc(), Producto.nombre.asc()).all()
    return [_publico(producto) for producto in productos]


def _obtener(db: Session, producto_id) -> Producto:
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto is None:
        raise AppError(404, "Producto no encontrado.")
    return producto


def crear_producto(db: Session, data) -> dict:
    nombre = data.nombre.strip()
    imagen_url = (data.imagen_url or "").strip()

    if not nombre:
        raise AppError(400, "El nombre del producto es obligatorio.")

    producto = Producto(
        nombre=nombre,
        categoria=data.categoria,
        precio=data.precio,
        imagen_url=imagen_url,
        activo=data.activo,
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return _publico(producto)


def actualizar_producto(db: Session, producto_id, data) -> dict:
    producto = _obtener(db, producto_id)
    cambios = data.model_dump(exclude_unset=True)

    if "nombre" in cambios and cambios["nombre"] is not None:
        nombre = cambios["nombre"].strip()
        if not nombre:
            raise AppError(400, "El nombre del producto es obligatorio.")
        producto.nombre = nombre

    if "categoria" in cambios and cambios["categoria"] is not None:
        producto.categoria = cambios["categoria"]

    if "precio" in cambios and cambios["precio"] is not None:
        producto.precio = cambios["precio"]

    if "imagen_url" in cambios and cambios["imagen_url"] is not None:
        producto.imagen_url = cambios["imagen_url"].strip()

    if "activo" in cambios and cambios["activo"] is not None:
        producto.activo = cambios["activo"]

    db.commit()
    db.refresh(producto)
    return _publico(producto)


def eliminar_producto(db: Session, producto_id) -> dict:
    producto = _obtener(db, producto_id)
    db.delete(producto)
    db.commit()
    return {"message": "Producto eliminado correctamente."}
