from datetime import datetime, timezone
import os

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.services import panel as panel_service
from app.services import panel_exportar as panel_exportar_service
from app.models.product_order import PedidoProducto, PedidoProductoItem
from sqlalchemy import func
from app.services.auditoria import registrar_auditoria

router = APIRouter()


@router.get("")
def obtener_panel(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    """Solo Super Administrador. Datos del panel de administración."""
    return panel_service.obtener_panel(db)


@router.get("/historial-compras")
def obtener_historial_compras_tienda(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    """Historial unificado de compras de planes y productos. Solo Super Administrador."""
    return panel_service.obtener_historial_compras_tienda(db)


@router.get("/ventas-productos")
def obtener_ventas_productos(
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    """Resumen de ventas de productos y pedidos por estado."""
    estados = dict(
        db.query(PedidoProducto.estado, func.count(PedidoProducto.id))
        .group_by(PedidoProducto.estado).all()
    )
    ingresos = (
        db.query(func.coalesce(func.sum(PedidoProducto.total), 0))
        .filter(PedidoProducto.estado.in_(["PAGADA", "ENVIADO", "ENTREGADO"]))
        .scalar() or 0
    )
    ventas_mes = (
        db.query(func.coalesce(func.sum(PedidoProducto.total), 0))
        .filter(
            PedidoProducto.estado.in_(["PAGADA", "ENVIADO", "ENTREGADO"]),
            func.date_trunc("month", PedidoProducto.creado_en) == func.date_trunc("month", func.now()),
        ).scalar() or 0
    )
    ingresos_por_mes = (
        db.query(
            func.to_char(func.date_trunc("month", PedidoProducto.creado_en), "YYYY-MM").label("mes"),
            func.coalesce(func.sum(PedidoProducto.total), 0).label("ingresos"),
        )
        .filter(PedidoProducto.estado.in_(["PAGADA", "ENVIADO", "ENTREGADO"]))
        .group_by(func.date_trunc("month", PedidoProducto.creado_en))
        .order_by(func.date_trunc("month", PedidoProducto.creado_en).desc())
        .limit(12).all()
    )
    mas_vendidos = (
        db.query(
            PedidoProductoItem.nombre_producto,
            func.coalesce(func.sum(PedidoProductoItem.cantidad), 0).label("unidades"),
            func.coalesce(func.sum(PedidoProductoItem.subtotal), 0).label("total"),
        )
        .join(PedidoProducto, PedidoProducto.id == PedidoProductoItem.pedido_id)
        .filter(PedidoProducto.estado.in_(["PAGADA", "ENVIADO", "ENTREGADO"]))
        .group_by(PedidoProductoItem.nombre_producto)
        .order_by(func.sum(PedidoProductoItem.cantidad).desc())
        .limit(10).all()
    )
    return {
        "ingresosTotales": int(ingresos),
        "ingresosMes": int(ventas_mes),
        "ingresosPorMes": [{"mes": mes, "ingresos": int(valor)} for mes, valor in reversed(ingresos_por_mes)],
        "pedidosPorEstado": estados,
        "productosMasVendidos": [
            {"producto": nombre, "unidades": int(unidades), "total": int(total)}
            for nombre, unidades, total in mas_vendidos
        ],
    }


@router.get("/evolucion")
def obtener_evolucion(
    meses: int = Query(12, ge=3, le=24),
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    """Solo Super Administrador. Evolución mensual del sistema."""
    return panel_service.obtener_evolucion_mensual(db, meses=meses)


@router.get("/exportar/{tabla}")
def exportar_tabla(
    tabla: str,
    filtro: str | None = None,
    buscar: str | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_admin),
):
    """Solo Super Administrador. Exporta la tabla solicitada a un archivo Excel."""
    ruta = panel_exportar_service.exportar_tabla_excel(db, tabla, filtro, buscar)
    registrar_auditoria(
        db,
        usuario=actual,
        accion="EXPORTAR_PANEL",
        entidad="panel",
        nota=tabla,
        request=request,
    )
    fecha_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return FileResponse(
        path=ruta,
        filename=f"panel_{tabla}_{fecha_str}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(os.remove, ruta),
    )
