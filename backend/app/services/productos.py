import io
import uuid

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.product import Producto
from app.models.user import Rol, Usuario
from app.services.notificaciones import notificar
from app.services.perfil import UPLOADS_DIR

MAX_IMAGEN_BYTES = 3 * 1024 * 1024  # 3 MB
FORMATOS_IMAGEN = {"JPEG", "PNG", "WEBP"}
LADO_MAXIMO_IMAGEN = 900
PRODUCTOS_DIR = UPLOADS_DIR / "productos"
URL_PRODUCTOS = "/api/uploads/productos"



def _categoria(valor: str) -> str:
    limpia = " ".join(valor.split())
    if len(limpia) < 2 or len(limpia) > 40:
        raise AppError(400, "La categoría debe tener entre 2 y 40 caracteres.")
    return limpia


def _alertar_stock_bajo(db: Session, producto: Producto) -> None:
    if producto.stock > 5:
        return
    administradores = (
        db.query(Usuario)
        .join(Rol, Usuario.rol_id == Rol.id)
        .filter(Rol.codigo == "SUPER_ADMINISTRADOR", Usuario.estado == "ACTIVO")
        .all()
    )
    estado = "agotado" if producto.stock == 0 else f"con solo {producto.stock} unidades disponibles"
    for administrador in administradores:
        notificar(
            db, usuario_id=administrador.id, tipo="STOCK_BAJO",
            titulo="Alerta de inventario",
            mensaje=f"El producto {producto.nombre} está {estado}. Revisa Gestión de tienda.",
            commit=False,
        )


def _publico(producto: Producto) -> dict:
    return {
        "id": str(producto.id),
        "nombre": producto.nombre,
        "categoria": producto.categoria,
        "precio": producto.precio,
        "imagen_url": producto.imagen_url,
        "activo": producto.activo,
        "stock": producto.stock,
        "agotado": producto.stock <= 0,
        "stock_bajo": 0 < producto.stock <= 5,
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
        categoria=_categoria(data.categoria),
        precio=data.precio,
        imagen_url=imagen_url,
        activo=data.activo,
        stock=data.stock,
    )
    db.add(producto)
    db.flush()
    _alertar_stock_bajo(db, producto)
    db.commit()
    db.refresh(producto)
    return _publico(producto)


def actualizar_producto(db: Session, producto_id, data) -> dict:
    producto = _obtener(db, producto_id)
    stock_anterior = producto.stock
    cambios = data.model_dump(exclude_unset=True)

    if "nombre" in cambios and cambios["nombre"] is not None:
        nombre = cambios["nombre"].strip()
        if not nombre:
            raise AppError(400, "El nombre del producto es obligatorio.")
        producto.nombre = nombre

    if "categoria" in cambios and cambios["categoria"] is not None:
        producto.categoria = _categoria(cambios["categoria"])

    if "precio" in cambios and cambios["precio"] is not None:
        producto.precio = cambios["precio"]

    if "imagen_url" in cambios and cambios["imagen_url"] is not None:
        producto.imagen_url = cambios["imagen_url"].strip()

    if "activo" in cambios and cambios["activo"] is not None:
        producto.activo = cambios["activo"]

    if "stock" in cambios and cambios["stock"] is not None:
        producto.stock = cambios["stock"]

    if stock_anterior > 5 and producto.stock <= 5:
        _alertar_stock_bajo(db, producto)
    db.commit()
    db.refresh(producto)
    return _publico(producto)


def eliminar_producto(db: Session, producto_id) -> dict:
    producto = _obtener(db, producto_id)
    db.delete(producto)
    db.commit()
    return {"message": "Producto eliminado correctamente."}


def guardar_imagen(contenido: bytes) -> dict:
    """Valida y optimiza la imagen de un producto; devuelve su URL pública."""
    if not contenido:
        raise AppError(400, "Selecciona una imagen.")
    if len(contenido) > MAX_IMAGEN_BYTES:
        raise AppError(400, "La imagen no puede superar los 3 MB.")
    try:
        with Image.open(io.BytesIO(contenido)) as img:
            if img.format not in FORMATOS_IMAGEN:
                raise AppError(400, "Formato no permitido. Usa JPG, PNG o WEBP.")
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                fondo = Image.new("RGB", img.size, (255, 255, 255))
                fondo.paste(img, mask=img.split()[-1])
                img = fondo
            else:
                img = img.convert("RGB")
            img.thumbnail((LADO_MAXIMO_IMAGEN, LADO_MAXIMO_IMAGEN), Image.Resampling.LANCZOS)
            salida = io.BytesIO()
            img.save(salida, format="JPEG", quality=85)
    except AppError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise AppError(400, "El archivo no es una imagen válida.")

    PRODUCTOS_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}.jpg"
    (PRODUCTOS_DIR / nombre).write_bytes(salida.getvalue())
    return {"imagen_url": f"{URL_PRODUCTOS}/{nombre}"}
