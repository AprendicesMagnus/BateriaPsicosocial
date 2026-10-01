import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.organization import Area, Organizacion
from app.models.evaluation import Evaluacion, EvaluacionParticipante
from app.models.user import Usuario

settings = get_settings()


def listar_reportes_por_area(db: Session, actual: Usuario) -> list[dict]:
    rol = actual.rol.codigo
    if rol == "SUPER_ADMINISTRADOR":
        query_areas = db.query(Area).options(joinedload(Area.organizacion))
    elif rol in {"EVALUADOR_SST", "RESPONSABLE_SST"}:
        if not actual.organizacion_id:
            return []
        query_areas = (
            db.query(Area)
            .options(joinedload(Area.organizacion))
            .filter(Area.organizacion_id == actual.organizacion_id)
        )
    else:
        raise AppError(403, "No tiene permisos para consultar reportes.")

    areas = query_areas.order_by(Area.nombre.asc()).all()

    reportes = []
    for area in areas:
        evaluacion_reciente = (
            db.query(Evaluacion)
            .filter(Evaluacion.organizacion_id == area.organizacion_id)
            .order_by(Evaluacion.creado_en.desc())
            .first()
        )
        evaluacion_id = str(evaluacion_reciente.id) if evaluacion_reciente else None

        count_completados = 0
        if evaluacion_reciente:
            count_completados = (
                db.query(func.count(func.distinct(EvaluacionParticipante.trabajador_id)))
                .join(Usuario, Usuario.id == EvaluacionParticipante.trabajador_id)
                .filter(
                    EvaluacionParticipante.evaluacion_id == evaluacion_reciente.id,
                    Usuario.area_id == area.id,
                    EvaluacionParticipante.estado == "COMPLETADA",
                )
                .scalar()
                or 0
            )

        estado = "listo" if count_completados >= settings.min_grupo_anonimato else "restringido"
        color = "#1F9D55" if estado == "listo" else "#D64545"

        reportes.append({
            "id": str(area.id),
            "areaId": str(area.id),
            "titulo": f"Reporte por Área · {area.nombre}",
            "descripcion": f"Organización: {area.organizacion.nombre} · {count_completados} respuestas registradas",
            "areaNombre": area.nombre,
            "organizacionId": str(area.organizacion_id),
            "organizacionNombre": area.organizacion.nombre,
            "evaluacionId": evaluacion_id,
            "participantesCompletados": count_completados,
            "minRequerido": settings.min_grupo_anonimato,
            "estado": estado,
            "color": color,
        })

    return reportes
