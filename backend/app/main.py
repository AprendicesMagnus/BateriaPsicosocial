from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import router as api_v1_router
from app.core.config import get_settings
from app.core.errors import AppError

settings = get_settings()

app = FastAPI(
    title="Bateria de Riesgo Psicosocial",
    version="1.0.0",
    description="API para la aplicacion de la Bateria de Riesgo Psicosocial en MiPymes",
)

if settings.env.lower() == "production":
    cors_origins = [settings.frontend_url]
else:
    cors_origins = list({
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5176",
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_ETIQUETAS_CAMPO = {
    "nombre": "El nombre",
    "apellido": "El apellido",
    "usuarioNombre": "El nombre del responsable",
    "usuarioApellido": "El apellido del responsable",
    "usuarioEmail": "El correo del usuario",
    "usuarioPassword": "La contraseña",
    "password": "La contraseña",
    "email": "El correo electrónico",
    "nit": "El NIT",
    "municipio": "La ciudad o municipio",
    "numeroTrabajadores": "El número de trabajadores",
    "telefono": "El teléfono",
    "numeroTarjeta": "El número de tarjeta",
    "nombreTarjeta": "El nombre en la tarjeta",
    "vencimiento": "La fecha de vencimiento",
    "cvv": "El código de seguridad (CVV)",
    "cantidad": "La cantidad",
    "cargo": "El cargo",
    "numeroIdentificacion": "El número de identificación",
    "tipo": "El tipo de código",
}


def _traducir_error(error: dict) -> str:
    campo = ".".join(str(p) for p in error.get("loc", ()) if p not in ("body", "query", "path"))
    etiqueta = _ETIQUETAS_CAMPO.get(campo, f"El campo '{campo}'" if campo else "El dato")
    tipo = error.get("type", "")
    ctx = error.get("ctx") or {}
    mensaje = error.get("msg", "")
    if tipo == "missing":
        return f"{etiqueta} es obligatorio."
    if tipo == "string_pattern_mismatch":
        return f"{etiqueta} contiene caracteres o un formato no permitidos."
    if tipo == "string_too_short":
        return f"{etiqueta} debe tener al menos {ctx.get('min_length')} caracteres."
    if tipo == "string_too_long":
        return f"{etiqueta} no puede superar {ctx.get('max_length')} caracteres."
    if tipo in {"greater_than", "greater_than_equal", "less_than", "less_than_equal"}:
        return f"{etiqueta} está fuera del rango permitido."
    if tipo in {"int_parsing", "int_from_float", "float_parsing"}:
        return f"{etiqueta} debe ser un número válido."
    if "email" in mensaje.lower():
        return f"{etiqueta} no es un correo válido."
    if tipo == "value_error":
        return f"{etiqueta}: {mensaje.removeprefix('Value error, ')}"
    return f"{etiqueta} no es válido."


@app.exception_handler(AppError)
async def manejar_app_error(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RequestValidationError)
async def manejar_error_validacion(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errores = exc.errors()
    primero = errores[0] if errores else {}
    mensaje = _traducir_error(primero)
    return JSONResponse(
        status_code=422,
        content={"error": mensaje, "detail": jsonable_encoder(errores)},
    )


# Fotos de perfil (se guardan en backend/uploads). Solo se sirven archivos estáticos.
from app.services.perfil import UPLOADS_DIR  # noqa: E402

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(api_v1_router)


# ---------------------------------------------------------------------------
# Scheduler de recordatorios automáticos (Punto 2)
# ---------------------------------------------------------------------------
import logging
from apscheduler.schedulers.background import BackgroundScheduler

_scheduler = BackgroundScheduler()

logger = logging.getLogger(__name__)


def _tarea_recordatorios_diarios() -> None:
    """Función ejecutada por el scheduler: abre su propia sesión de BD."""
    from app.db.session import SessionLocal
    from app.services.notificaciones import _ejecutar_envio_recordatorios

    db = SessionLocal()
    try:
        resultado = _ejecutar_envio_recordatorios(db)
        logger.info(
            "Scheduler recordatorios: enviados=%s, omitidos=%s",
            resultado["enviadosCount"],
            resultado["omitidosCount"],
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error en scheduler de recordatorios: %s", exc, exc_info=True)
    finally:
        db.close()


@app.on_event("startup")
def iniciar_scheduler() -> None:
    _scheduler.add_job(
        _tarea_recordatorios_diarios,
        "cron",
        hour=8,
        minute=0,
        id="recordatorios_diarios",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler de recordatorios iniciado (disparo diario a las 08:00).")


@app.on_event("shutdown")
def detener_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler de recordatorios detenido.")
