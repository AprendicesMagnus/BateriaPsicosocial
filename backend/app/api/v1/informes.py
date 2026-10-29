import os
import re
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.roles import ROLES_EVALUADOR
from app.api.deps import (
    asegurar_acceso_organizacion_db,
    get_current_user,
    puede_acceder_organizacion,
    require_generador_informes,
    require_gestor,
)
from app.core.errors import AppError
from app.db.session import get_db
from app.models.evaluation import Evaluacion, Informe
from app.models.organization import Organizacion
from app.models.user import Usuario
from app.services import auditoria as auditoria_service
from app.services import informes as informes_service
from app.services.informes_excel import generar_zip_informes_empresa

router = APIRouter()


class InformeIndividualCreateRequest(BaseModel):
    evaluacionId: UUID
    participanteId: UUID


class InformeAgrupadoCreateRequest(BaseModel):
    evaluacionId: UUID
    areaId: UUID | None = None


def _asegurar_evaluacion_accesible(db: Session, evaluacion_id: UUID, actual: Usuario) -> None:
    evaluacion = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if evaluacion is None:
        raise AppError(404, "Evaluación no encontrada.")
    asegurar_acceso_organizacion_db(db, actual, evaluacion.organizacion_id)


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
        "codigoVerificacion": informe.codigo_verificacion,
        "hashSha256": informe.hash_sha256,
    }


@router.post("/agrupado")
def generar_informe_agrupado(
    data: InformeAgrupadoCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_generador_informes),
):
    """Genera y descarga en un ZIP las plantillas Excel llenas, filtradas a la evaluación
    (y, si se indica, al área) seleccionada."""
    evaluacion = db.query(Evaluacion).filter(Evaluacion.id == data.evaluacionId).first()
    if evaluacion is None:
        raise AppError(404, "Evaluación no encontrada.")
    asegurar_acceso_organizacion_db(db, actual, evaluacion.organizacion_id)

    try:
        archivo_zip = generar_zip_informes_empresa(
            db=db,
            organizacion_id=evaluacion.organizacion_id,
            evaluacion_id=data.evaluacionId,
            area_id=data.areaId,
            aplicar_minimo_anonimato=True,
        )
    except FileNotFoundError as exc:
        raise AppError(500, str(exc))
    except ValueError as exc:
        raise AppError(400, str(exc))

    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="INFORME_AGRUPADO_GENERADO",
        entidad="Evaluacion",
        entidad_id=str(data.evaluacionId),
        request=request,
    )

    nombre_archivo = f"Informe_Agrupado_{data.evaluacionId}.zip"
    return StreamingResponse(
        archivo_zip,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get("/verificar/{codigo}")
def verificar_informe(codigo: str, db: Session = Depends(get_db)):
    return informes_service.obtener_verificacion_informe(db, codigo)


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
    es_evaluador = actual.rol.codigo in ROLES_EVALUADOR
    misma_org = puede_acceder_organizacion(db, actual, informe.evaluacion.organizacion_id)

    if informe.tipo == "INDIVIDUAL":
        es_dueno = actual.id == informe.trabajador_id
        es_gestor_autorizado = (es_admin or es_evaluador) and misma_org
        if not (es_dueno or es_gestor_autorizado):
            raise AppError(403, "No tiene permisos para descargar este informe individual.")
    elif informe.tipo == "AGRUPADO":
        es_responsable = actual.rol.codigo == "RESPONSABLE_SST"
        es_admin_empresa = actual.rol.codigo == "ADMINISTRADOR"  # solo de las empresas que creó
        es_gestor_autorizado = (es_admin or es_evaluador or es_responsable or es_admin_empresa) and misma_org
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


@router.get("/empresa/{organizacion_id}/excel/zip")
def descargar_informes_empresa_zip(
    organizacion_id: UUID,
    request: Request,
    evaluacion_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_generador_informes),
):
    """ZIP con los informes Excel llenos.

    Sin evaluacion_id se incluyen todas las evaluaciones de la empresa (cada enlace de
    pacientes es una evaluación distinta); con evaluacion_id, solo esa evaluación.
    """
    asegurar_acceso_organizacion_db(db, actual, organizacion_id)

    try:
        archivo_zip = generar_zip_informes_empresa(
            db=db,
            organizacion_id=organizacion_id,
            evaluacion_id=evaluacion_id,
        )
    except FileNotFoundError as exc:
        raise AppError(500, str(exc))
    except ValueError as exc:
        raise AppError(400, str(exc))

    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="INFORMES_EXCEL_DESCARGADOS",
        entidad="Evaluacion" if evaluacion_id else "Organizacion",
        entidad_id=str(evaluacion_id or organizacion_id),
        request=request,
    )

    organizacion = db.query(Organizacion).filter(Organizacion.id == organizacion_id).first()
    nombre_empresa = re.sub(r"[^0-9A-Za-z]+", "_", organizacion.nombre if organizacion else "").strip("_")
    nombre_archivo = f"Informes_{nombre_empresa or organizacion_id}.zip"

    return StreamingResponse(
        archivo_zip,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )