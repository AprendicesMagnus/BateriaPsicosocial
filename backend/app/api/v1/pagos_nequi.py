from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_admin, require_comprador
from app.core.errors import AppError
from app.core.config import get_settings
from app.models.commercial import Compra, Pago
from app.models.product_order import PedidoProducto, PagoPedidoProducto
from app.models.user import Usuario
from app.models.organization import Organizacion
from app.services.notificaciones import notificar

router = APIRouter()
BACKEND_DIR = Path(__file__).resolve().parents[3]
_STORAGE_ROOT = Path(get_settings().storage_path)
if not _STORAGE_ROOT.is_absolute():
    _STORAGE_ROOT = BACKEND_DIR / _STORAGE_ROOT
PAYMENTS_DIR = _STORAGE_ROOT.resolve() / "nequi-payments"
PAYMENTS_DIR.mkdir(parents=True, exist_ok=True)
NEQUI_CONFIG_PATH = PAYMENTS_DIR / "nequi-config.json"
DEFAULT_NEQUI_CONFIG = {
    "llave": "322 712 2675",
    "titular": "Juan Parra",
}


class NequiConfigUpdate(BaseModel):
    llave: str = Field(min_length=5, max_length=60)
    titular: str = Field(min_length=2, max_length=100)


def _leer_configuracion_nequi() -> dict:
    """Lee la configuración pública de Nequi; conserva valores predeterminados si aún no existe."""
    config = dict(DEFAULT_NEQUI_CONFIG)
    try:
        if NEQUI_CONFIG_PATH.is_file():
            almacenada = json.loads(NEQUI_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(almacenada, dict):
                llave = almacenada.get("llave")
                titular = almacenada.get("titular")
                if isinstance(llave, str) and llave.strip():
                    config["llave"] = llave.strip()
                if isinstance(titular, str) and titular.strip():
                    config["titular"] = titular.strip()
    except (OSError, json.JSONDecodeError):
        # Si el archivo está dañado no se interrumpe el checkout; se usan los valores base.
        pass
    return config


def _guardar_configuracion_nequi(llave: str, titular: str) -> None:
    """Guarda de forma atómica para evitar archivos parciales si el proceso se interrumpe."""
    NEQUI_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporal = NEQUI_CONFIG_PATH.with_suffix(".tmp")
    temporal.write_text(
        json.dumps({"llave": llave, "titular": titular}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporal.replace(NEQUI_CONFIG_PATH)


def _qr_path():
    default_dir = BACKEND_DIR / "storage" / "nequi-payments"
    for directory in (PAYMENTS_DIR, default_dir):
        for suffix in ("png", "jpg"):
            candidate = directory / f"nequi-qr.{suffix}"
            if candidate.is_file():
                return candidate
    return None
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}


def _save_image(file: UploadFile, prefix: str) -> str:
    content_type = (file.content_type or "").lower()
    extension = ALLOWED_TYPES.get(content_type)
    if not extension:
        raise AppError(400, "El archivo debe ser una imagen JPG, JPEG o PNG.")
    data = file.file.read(MAX_FILE_SIZE + 1)
    if not data or len(data) > MAX_FILE_SIZE:
        raise AppError(400, "La imagen debe tener contenido y no superar 5 MB.")
    # Verificación de firma binaria: no confiar únicamente en Content-Type.
    valid = data.startswith(b"\xff\xd8\xff") if extension == ".jpg" else data.startswith(b"\x89PNG\r\n\x1a\n")
    if not valid:
        raise AppError(400, "El contenido del archivo no corresponde a una imagen válida.")
    name = f"{prefix}-{uuid.uuid4().hex}{extension}"
    path = PAYMENTS_DIR / name
    path.write_bytes(data)
    return name


def _public_payment(p, db=None):
    reviewer = db.query(Usuario).filter(Usuario.id == p.revisado_por_id).first() if db is not None and p.revisado_por_id else None
    return {
        "id": str(p.id), "metodo": p.metodo, "referencia": p.referencia,
        "monto": p.monto, "estado": p.estado,
        "comprobanteUrl": bool(p.comprobante_path),
        "observaciones": p.observaciones,
        "revisadoEn": p.revisado_en.isoformat() if p.revisado_en else None,
        "revisadoPorId": str(p.revisado_por_id) if p.revisado_por_id else None,
        "revisadoPor": f"{reviewer.nombre} {reviewer.apellido}" if reviewer else None,
        "procesadoEn": p.procesado_en.isoformat(),
    }


@router.get("/configuracion")
def configuracion_nequi(actual: Usuario = Depends(require_comprador)):
    config = _leer_configuracion_nequi()
    qr = _qr_path()
    return {
        "qrDisponible": qr is not None,
        "qrUrl": "/api/pagos-nequi/qr" if qr is not None else None,
        "llave": config["llave"],
        "titular": config["titular"],
        "instrucciones": "Escanea el código QR desde Nequi, verifica el valor exacto y realiza la transferencia. Después adjunta el comprobante para revisión.",
    }


@router.put("/configuracion")
def actualizar_configuracion_nequi(
    data: NequiConfigUpdate,
    actual: Usuario = Depends(require_admin),
):
    llave = re.sub(r"\s+", " ", data.llave).strip()
    titular = re.sub(r"\s+", " ", data.titular).strip()

    # La llave puede ser celular, identificación, correo o alias Bre-B.
    # Se permite puntuación para no limitar formatos válidos de alias/correo.
    if not 5 <= len(llave) <= 60 or any(ord(char) < 32 for char in llave):
        raise AppError(400, "La llave debe tener entre 5 y 60 caracteres válidos.")
    if len(titular) < 2 or any(ord(char) < 32 for char in titular):
        raise AppError(400, "Escribe un nombre de titular válido.")

    _guardar_configuracion_nequi(llave, titular)
    return {"ok": True, "llave": llave, "titular": titular}


@router.get("/qr")
def obtener_qr():
    if _qr_path() is None:
        raise AppError(404, "El código QR de Nequi todavía no está configurado.")
    path = _qr_path()
    return FileResponse(path, media_type="image/png" if path.suffix == ".png" else "image/jpeg", filename=path.name, headers={"Cache-Control": "no-store, max-age=0"})


@router.put("/qr")
def actualizar_qr(file: UploadFile = File(...), actual: Usuario = Depends(require_admin)):
    # Se acepta PNG/JPG y se conserva una copia con extensión real.
    relative = _save_image(file, "qr")
    source = PAYMENTS_DIR / relative
    for old in PAYMENTS_DIR.glob("nequi-qr.*"):
        old.unlink(missing_ok=True)
    target = PAYMENTS_DIR / f"nequi-qr{source.suffix}"
    source.replace(target)
    return {"ok": True, "qrUrl": "/api/pagos-nequi/qr"}


def _find_payment(db: Session, tipo: str, object_id: uuid.UUID, user: Usuario, lock=False):
    if tipo == "bateria":
        q = db.query(Compra).filter(Compra.id == object_id)
        if lock: q = q.with_for_update()
        obj = q.first()
        if obj is None: raise AppError(404, "Compra no encontrada.")
        if user.rol.codigo != "SUPER_ADMINISTRADOR" and obj.usuario_id != user.id:
            raise AppError(403, "No tiene acceso a esta compra.")
        payment_q = db.query(Pago).filter(Pago.compra_id == obj.id, Pago.metodo == "nequi").order_by(Pago.procesado_en.desc())
        if lock: payment_q = payment_q.with_for_update()
    elif tipo == "producto":
        q = db.query(PedidoProducto).filter(PedidoProducto.id == object_id)
        if lock:
            # Bloquear solamente la fila principal del pedido. Si se combina
            # FOR UPDATE con joinedload(items), PostgreSQL rechaza el bloqueo
            # del lado nullable generado por el LEFT OUTER JOIN.
            q = q.with_for_update()
        else:
            q = q.options(joinedload(PedidoProducto.items))
        obj = q.first()
        if obj is None: raise AppError(404, "Pedido no encontrado.")
        if user.rol.codigo != "SUPER_ADMINISTRADOR" and obj.usuario_id != user.id:
            raise AppError(403, "No tiene acceso a este pedido.")
        payment_q = db.query(PagoPedidoProducto).filter(PagoPedidoProducto.pedido_id == obj.id, PagoPedidoProducto.metodo == "nequi").order_by(PagoPedidoProducto.procesado_en.desc())
        if lock: payment_q = payment_q.with_for_update()
    else:
        raise AppError(400, "Tipo de compra no válido.")
    return obj, payment_q.first()


@router.post("/{tipo}/{object_id}/iniciar")
def iniciar_pago_nequi(tipo: str, object_id: uuid.UUID, db: Session = Depends(get_db), actual: Usuario = Depends(require_comprador)):
    if tipo == "bateria":
        from app.services.compras import _expirar_compras_vencidas
        _expirar_compras_vencidas(db, usuario_id=actual.id)
    elif tipo == "producto":
        from app.services.pedidos_productos import _expirar_pedidos_vencidos
        _expirar_pedidos_vencidos(db, usuario_id=actual.id)
    obj, payment = _find_payment(db, tipo, object_id, actual, lock=True)
    if obj.estado in {"PAGADA", "ENVIADO", "ENTREGADO"}:
        raise AppError(409, "Esta compra ya está pagada.")
    if obj.estado in {"CANCELADA", "EXPIRADA"}:
        raise AppError(409, "Esta compra ya no admite pagos.")
    if _qr_path() is None:
        raise AppError(503, "El administrador todavía no ha configurado el QR de Nequi.")
    # No iniciar Nequi si existe una transacción Wompi histórica aún en curso para
    # la misma compra: evita cobrar dos veces durante la transición de pasarela.
    if tipo == "bateria":
        wompi_en_curso = db.query(Pago.id).filter(
            Pago.compra_id == obj.id, Pago.metodo == "wompi",
            Pago.wompi_transaction_id.isnot(None), Pago.wompi_status == "PENDING",
        ).first()
    else:
        wompi_en_curso = db.query(PagoPedidoProducto.id).filter(
            PagoPedidoProducto.pedido_id == obj.id, PagoPedidoProducto.metodo == "wompi",
            PagoPedidoProducto.wompi_transaction_id.isnot(None), PagoPedidoProducto.wompi_status == "PENDING",
        ).first()
    if wompi_en_curso:
        raise AppError(409, "Esta compra todavía tiene una transacción Wompi histórica en proceso. Espera su confirmación antes de iniciar un pago Nequi.")
    if payment is not None and payment.estado == "RECHAZADO":
        if tipo == "producto":
            from app.models.product import Producto
            from app.services.productos import maneja_stock
            if obj.stock_reintegrado:
                for item in obj.items:
                    if item.producto_id is None:
                        continue
                    product = db.query(Producto).filter(Producto.id == item.producto_id).with_for_update().first()
                    if product is not None and maneja_stock(product):
                        if product.stock < item.cantidad:
                            raise AppError(409, f"Stock insuficiente para reintentar {item.nombre_producto}.")
                        product.stock -= item.cantidad
                obj.stock_reintegrado = False
        payment = None
    if payment is None:
        reference = f"NEQUI-{uuid.uuid4().hex[:20].upper()}"
        if tipo == "bateria":
            payment = Pago(compra_id=obj.id, metodo="nequi", referencia=reference, monto=obj.total, estado="PENDIENTE", mensaje_respuesta="Esperando comprobante de transferencia Nequi.")
        else:
            payment = PagoPedidoProducto(pedido_id=obj.id, metodo="nequi", referencia=reference, monto=obj.total, estado="PENDIENTE", mensaje_respuesta="Esperando comprobante de transferencia Nequi.")
        obj.estado = "PENDIENTE"
        db.add(payment); db.commit(); db.refresh(payment)
    config = _leer_configuracion_nequi()
    return {
        "id": str(obj.id),
        "tipo": tipo,
        "total": obj.total,
        "estado": obj.estado,
        "pago": _public_payment(payment, db),
        "qrUrl": "/api/pagos-nequi/qr",
        "llave": config["llave"],
        "titular": config["titular"],
    }


@router.post("/{tipo}/{object_id}/comprobante")
def adjuntar_comprobante(tipo: str, object_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db), actual: Usuario = Depends(require_comprador)):
    obj, payment = _find_payment(db, tipo, object_id, actual, lock=True)
    if obj.estado != "PENDIENTE" or payment is None or payment.estado != "PENDIENTE":
        raise AppError(409, "No existe un pago pendiente que admita comprobante.")
    if payment.comprobante_path:
        raise AppError(409, "Ya se adjuntó un comprobante para este intento de pago.")
    relative = _save_image(file, "receipt")
    payment.comprobante_path = relative
    payment.estado = "PENDIENTE_VERIFICACION"
    payment.mensaje_respuesta = "Comprobante recibido. Pendiente de verificación administrativa."
    obj.estado = "PENDIENTE_VERIFICACION"
    db.commit(); db.refresh(payment)
    return {"ok": True, "estado": obj.estado, "pago": _public_payment(payment, db)}


@router.get("/comprobante/{tipo}/{object_id}")
def obtener_comprobante(tipo: str, object_id: uuid.UUID, db: Session = Depends(get_db), actual: Usuario = Depends(get_current_user)):
    _, payment = _find_payment(db, tipo, object_id, actual)
    if payment is None or not payment.comprobante_path:
        raise AppError(404, "No hay comprobante disponible para esta compra.")
    path = PAYMENTS_DIR / Path(payment.comprobante_path).name
    if not path.is_file():
        raise AppError(404, "El archivo del comprobante no está disponible.")
    return FileResponse(path, media_type="image/png" if path.suffix == ".png" else "image/jpeg", filename=path.name)


@router.get("/administracion")
def listar_pagos_admin(estado: str = "PENDIENTE_VERIFICACION", db: Session = Depends(get_db), actual: Usuario = Depends(require_admin)):
    estado = estado.upper()
    rows = []
    for p in db.query(Pago).filter(Pago.metodo == "nequi", Pago.estado == estado).order_by(Pago.procesado_en.desc()).all():
        c = db.query(Compra).options(joinedload(Compra.usuario)).filter(Compra.id == p.compra_id).first()
        if c:
            empresa = db.query(Organizacion).filter(Organizacion.id == c.organizacion_id).first() if c.organizacion_id else None
            rows.append({"tipo":"bateria", "compraId":str(c.id), "usuarioId":str(c.usuario_id), "usuario":f"{c.usuario.nombre} {c.usuario.apellido}", "empresa":empresa.nombre if empresa else "Sin empresa asociada", "empresaId":str(c.organizacion_id) if c.organizacion_id else None, "producto":c.bateria_nombre, "cantidad":c.cantidad, "total":c.total, "fecha":c.creado_en.isoformat(), "pago":_public_payment(p, db)})
    for p in db.query(PagoPedidoProducto).filter(PagoPedidoProducto.metodo == "nequi", PagoPedidoProducto.estado == estado).order_by(PagoPedidoProducto.procesado_en.desc()).all():
        o = db.query(PedidoProducto).options(joinedload(PedidoProducto.items)).filter(PedidoProducto.id == p.pedido_id).first()
        if o:
            u = db.query(Usuario).filter(Usuario.id == o.usuario_id).first()
            empresa = db.query(Organizacion).filter(Organizacion.id == o.organizacion_id).first() if o.organizacion_id else None
            rows.append({"tipo":"producto", "compraId":str(o.id), "usuarioId":str(o.usuario_id), "usuario":f"{u.nombre} {u.apellido}" if u else "Usuario", "empresa":empresa.nombre if empresa else "Sin empresa asociada", "producto":", ".join(f"{i.nombre_producto} x{i.cantidad}" for i in o.items), "total":o.total, "fecha":o.creado_en.isoformat(), "pago":_public_payment(p, db)})
    return sorted(rows, key=lambda x: x["fecha"], reverse=True)


@router.post("/administracion/{tipo}/{object_id}/aprobar")
def aprobar_pago(tipo: str, object_id: uuid.UUID, db: Session = Depends(get_db), actual: Usuario = Depends(require_admin)):
    obj, payment = _find_payment(db, tipo, object_id, actual, lock=True)
    if payment is None or payment.estado != "PENDIENTE_VERIFICACION" or not payment.comprobante_path:
        raise AppError(409, "El pago no está pendiente de verificación o no tiene comprobante.")
    if obj.estado == "PAGADA": raise AppError(409, "La compra ya fue aprobada.")
    if tipo == "bateria" and obj.organizacion_id is None:
        owner = db.query(Usuario).filter(Usuario.id == obj.usuario_id).first()
        if owner and owner.organizacion_id:
            obj.organizacion_id = owner.organizacion_id
    payment.estado = "APROBADO"; payment.revisado_por_id = actual.id; payment.revisado_en = datetime.now(timezone.utc); payment.mensaje_respuesta = "Pago aprobado manualmente por Nequi."
    obj.estado = "PAGADA"
    if tipo == "producto":
        notificar(db, usuario_id=obj.usuario_id, tipo="COMPRA_APROBADA", titulo="Compra de productos aprobada", mensaje=f"Tu pedido PED-{obj.id.hex[:10].upper()} fue aprobado.", commit=False)
    else:
        notificar(db, usuario_id=obj.usuario_id, tipo="COMPRA_APROBADA", titulo="Compra de baterías aprobada", mensaje=f"Tu compra de {obj.cantidad} batería(s) fue aprobada y ya está disponible.", commit=False)
    db.commit(); db.refresh(payment)
    return {"ok":True, "estado":obj.estado, "pago":_public_payment(payment, db)}


@router.post("/administracion/{tipo}/{object_id}/rechazar")
def rechazar_pago(tipo: str, object_id: uuid.UUID, observaciones: str, db: Session = Depends(get_db), actual: Usuario = Depends(require_admin)):
    observaciones = (observaciones or "").strip()
    if not observaciones or len(observaciones) > 500: raise AppError(400, "Las observaciones son obligatorias y no pueden superar 500 caracteres.")
    obj, payment = _find_payment(db, tipo, object_id, actual, lock=True)
    if payment is None or payment.estado != "PENDIENTE_VERIFICACION": raise AppError(409, "El pago no está pendiente de verificación.")
    payment.estado = "RECHAZADO"; payment.observaciones = observaciones; payment.revisado_por_id = actual.id; payment.revisado_en = datetime.now(timezone.utc); payment.mensaje_respuesta = "Pago rechazado. Consulta las observaciones administrativas."
    obj.estado = "RECHAZADO"
    if tipo == "producto":
        # Se reintegra inventario mediante la misma protección de idempotencia existente.
        from app.services.pedidos_productos import _reintegrar_stock
        _reintegrar_stock(db, obj)
    db.commit(); db.refresh(payment)
    return {"ok":True, "estado":obj.estado, "pago":_public_payment(payment, db)}
