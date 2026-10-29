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
