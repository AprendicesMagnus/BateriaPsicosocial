from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_gestor
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import Usuario
from app.services import auditoria as auditoria_service
from app.services import enlaces as enlaces_service

router = APIRouter()


class EnlaceCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)


class IniciarEnlaceRequest(BaseModel):
    # El paciente debe marcar la casilla del consentimiento informado
    aceptaConsentimiento: bool


@router.get("")
def listar_enlaces(
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return enlaces_service.listar_enlaces(db, actual)


@router.post("")
def crear_enlace(
    data: EnlaceCreate,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    resultado = enlaces_service.crear_enlace(db, data.nombre, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="CREAR_ENLACE_PACIENTES",
        entidad="Evaluacion",
        entidad_id=resultado["evaluacionId"],
        request=request,
    )
    return resultado


@router.delete("/{evaluacion_id}")
def eliminar_enlace(
    evaluacion_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    resultado = enlaces_service.eliminar_enlace(db, evaluacion_id, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="ELIMINAR_ENLACE_PACIENTES",
        entidad="Evaluacion",
        entidad_id=str(evaluacion_id),
        request=request,
    )
    return resultado


# ---- Endpoints públicos (sin sesión): los usa el paciente al abrir el enlace ----


@router.get("/publico/{token}")
def info_enlace(token: str, db: Session = Depends(get_db)):
    return enlaces_service.info_publica(db, token)


@router.post("/publico/{token}/iniciar")
def iniciar_enlace(
    token: str,
    data: IniciarEnlaceRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if not data.aceptaConsentimiento:
        raise AppError(400, "Debes aceptar el consentimiento informado para comenzar.")
    ip = request.client.host if request.client else None
    return enlaces_service.iniciar_como_invitado(db, token, ip)
