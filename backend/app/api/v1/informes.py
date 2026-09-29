import os
from uuid import UUID
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.api.deps import asegurar_acceso_organizacion, get_current_user, require_gestor
from app.core.errors import AppError
from app.db.session import get_db
from app.models.evaluation import Evaluacion, Informe
from app.models.user import Usuario
from app.services import auditoria as auditoria_service
from app.services import informes as informes_service

router = APIRouter()


class InformeIndividualCreateRequest(BaseModel):
    evaluacionId: UUID
    participanteId: UUID


class InformeAgrupadoCreateRequest(BaseModel):
    evaluacionId: UUID
    areaId: UUID | None = None
    formato: str = Field(default="PDF", pattern=r"^(PDF|EXCEL|CSV)$")


def _asegurar_evaluacion_accesible(db: Session, evaluacion_id: UUID, actual: Usuario) -> None:
    evaluacion = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if evaluacion is None:
        raise AppError(404, "Evaluación no encontrada.")
    asegurar_acceso_organizacion(actual, evaluacion.organizacion_id)


@router.get("")
def listar_informes(
    evaluacion_id: UUID | None = None,
    tipo: str | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return informes_service.listar_informes(db, actual, evaluacion_id=evaluacion_id, tipo=tipo)


@router.post("/individual")
def generar_informe_individual(
    data: InformeIndividualCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    _asegurar_evaluacion_accesible(db, data.evaluacionId, actual)
    informe = informes_service.generar_informe_individual(
        db, data.evaluacionId, data.participanteId, actual.id
    )
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="INFORME_INDIVIDUAL_GENERADO",
        entidad="Informe",
        entidad_id=str(informe.id),
        request=request,
    )
    return {
        "id": str(informe.id),
        "tipo": informe.tipo,
        "formato": informe.formato,
        "rutaArchivo": informe.ruta_archivo,
        "generadoEn": informe.generado_en.isoformat(),
        "anonimizado": informe.anonimizado,
    }


@router.post("/agrupado")
def generar_informe_agrupado(
    data: InformeAgrupadoCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    _asegurar_evaluacion_accesible(db, data.evaluacionId, actual)
    informe = informes_service.generar_informe_agrupado(
        db, data.evaluacionId, data.areaId, actual.id, data.formato
    )
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="INFORME_AGRUPADO_GENERADO",
        entidad="Informe",
        entidad_id=str(informe.id),
        request=request,
    )
    return {
        "id": str(informe.id),
        "tipo": informe.tipo,
        "formato": informe.formato,
        "rutaArchivo": informe.ruta_archivo,
        "generadoEn": informe.generado_en.isoformat(),
        "anonimizado": informe.anonimizado,
    }


@router.get("/{informe_id}/descargar")
def descargar_informe(
    informe_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    informe = (
        db.query(Informe)
        .options(joinedload(Informe.evaluacion))
        .filter(Informe.id == informe_id)
        .first()
    )
    if informe is None:
        raise AppError(404, "Informe no encontrado.")

    # Validar permisos de acceso según el tipo de informe
    es_admin = actual.rol.codigo == "SUPER_ADMINISTRADOR"
    es_evaluador = actual.rol.codigo == "EVALUADOR_SST"
    misma_org = es_admin or (actual.organizacion_id == informe.evaluacion.organizacion_id)

    if informe.tipo == "INDIVIDUAL":
        es_dueno = actual.id == informe.trabajador_id
        es_gestor_autorizado = (es_admin or es_evaluador) and misma_org
        if not (es_dueno or es_gestor_autorizado):
            raise AppError(403, "No tiene permisos para descargar este informe individual.")
    elif informe.tipo == "AGRUPADO":
        es_gestor_autorizado = (es_admin or es_evaluador) and misma_org
        if not es_gestor_autorizado:
            raise AppError(403, "No tiene permisos para descargar este informe agrupado.")
    else:
        raise AppError(403, "Tipo de informe no reconocido.")

    if not os.path.exists(informe.ruta_archivo):
        raise AppError(404, "El archivo solicitado no se encuentra en el almacenamiento.")

    filename = os.path.basename(informe.ruta_archivo)
    media_type = "application/pdf" if informe.formato == "PDF" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return FileResponse(
        path=informe.ruta_archivo,
        filename=filename,
        media_type=media_type,
    )
