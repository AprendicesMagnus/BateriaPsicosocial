from fastapi import APIRouter

from app.api.v1 import (
    auth,
    auditoria,
    compras,
    cuestionarios,
    enlaces,
    evaluaciones,
    indicadores,
    informes,
    notificaciones,
    organizaciones,
    pagos,
    prediccion,
    reportes,
    roles,
    # TODO: seguimiento_recomendaciones se quitó porque el archivo
    # app/api/v1/seguimiento_recomendaciones.py no se subió en el commit 8e877ea.
    # Cuando esté en el repo, volver a agregarlo aquí y en el include_router de abajo.
    usuarios,
)

router = APIRouter(prefix="/api")

router.include_router(auth.router, prefix="/auth", tags=["Autenticacion"])
router.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
router.include_router(roles.router, prefix="/roles", tags=["Roles"])
router.include_router(organizaciones.router, prefix="/organizaciones", tags=["Organizaciones"])
router.include_router(cuestionarios.router, prefix="/cuestionarios", tags=["Cuestionarios"])
router.include_router(evaluaciones.router, prefix="/evaluaciones", tags=["Evaluaciones"])
router.include_router(enlaces.router, prefix="/enlaces", tags=["Enlaces"])
router.include_router(informes.router, prefix="/informes", tags=["Informes"])
router.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])
router.include_router(indicadores.router, prefix="/indicadores", tags=["Indicadores"])
router.include_router(prediccion.router, prefix="/prediccion", tags=["Prediccion"])
router.include_router(notificaciones.router, prefix="/notificaciones", tags=["Notificaciones"])
router.include_router(auditoria.router, prefix="/auditoria", tags=["Auditoria"])
router.include_router(compras.router, prefix="/compras", tags=["Compras"])
router.include_router(pagos.router, prefix="/pagos", tags=["Pagos"])
# TODO: restaurar cuando exista el módulo:
# router.include_router(seguimiento_recomendaciones.router, prefix="/seguimiento-recomendaciones", tags=["SeguimientoRecomendaciones"])
