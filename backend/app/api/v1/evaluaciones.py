from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_gestor
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import EvaluacionCierre, EvaluacionCreate, FichaDatosRequest, RespuestaRequest
from app.services import auditoria as auditoria_service
from app.services import evaluaciones as evaluaciones_service
from app.services import tabulacion as tabulacion_service

router = APIRouter()


@router.get("")
def listar_evaluaciones(
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return evaluaciones_service.listar_evaluaciones(db, actual)


@router.get("/{evaluacion_id}")
def obtener_evaluacion(
    evaluacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return evaluaciones_service.obtener_evaluacion(db, evaluacion_id, actual)


@router.post("")
def crear_evaluacion(
    data: EvaluacionCreate,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    resultado = evaluaciones_service.crear_evaluacion(db, data, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="CREAR_EVALUACION",
        entidad="Evaluacion",
        entidad_id=resultado["id"],
        request=request,
    )
    return resultado


@router.post("/{evaluacion_id}/iniciar")
def iniciar_evaluacion(
    evaluacion_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    resultado = evaluaciones_service.iniciar_evaluacion(db, evaluacion_id, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="INICIAR_EVALUACION",
        entidad="Evaluacion",
        entidad_id=str(evaluacion_id),
        request=request,
    )
    return resultado


@router.post("/{evaluacion_id}/notificar")
def notificar_participantes(
    evaluacion_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return evaluaciones_service.notificar_participantes(db, evaluacion_id, actual, request)


@router.post("/{evaluacion_id}/finalizar")
def finalizar_evaluacion(
    evaluacion_id: UUID,
    data: EvaluacionCierre,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    resultado = evaluaciones_service.finalizar_evaluacion(db, evaluacion_id, data, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="FINALIZAR_EVALUACION",
        entidad="Evaluacion",
        entidad_id=str(evaluacion_id),
        request=request,
    )
    return resultado


@router.post("/{evaluacion_id}/consentimiento")
def registrar_consentimiento(
    evaluacion_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    ip = request.client.host if request.client else None
    return evaluaciones_service.registrar_consentimiento(db, evaluacion_id, actual, ip)


@router.get("/{evaluacion_id}/cuestionario")
def obtener_cuestionario_asignado(
    evaluacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return evaluaciones_service.obtener_cuestionario_asignado(db, evaluacion_id, actual)


@router.post("/{evaluacion_id}/respuestas")
def guardar_respuesta(
    evaluacion_id: UUID,
    data: RespuestaRequest,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return evaluaciones_service.guardar_respuesta(db, evaluacion_id, data, actual)


@router.post("/{evaluacion_id}/finalizar-cuestionario")
def finalizar_cuestionario(
    evaluacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return evaluaciones_service.finalizar_cuestionario(db, evaluacion_id, actual)


@router.get("/{evaluacion_id}/instrumentos")
def obtener_instrumentos_participante(
    evaluacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return evaluaciones_service.obtener_instrumentos_participante(db, evaluacion_id, actual)


@router.post("/{evaluacion_id}/ficha")
def guardar_ficha_datos(
    evaluacion_id: UUID,
    data: FichaDatosRequest,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return evaluaciones_service.guardar_ficha_datos(db, evaluacion_id, data, actual)


@router.get("/{evaluacion_id}/resultados")
def consultar_resultados(
    evaluacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return tabulacion_service.resultados_evaluacion(db, evaluacion_id, actual)

