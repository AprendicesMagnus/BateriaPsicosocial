import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.organization import Area, Organizacion
from app.models.evaluation import (
    Evaluacion,
    EvaluacionInstrumento,
    EvaluacionParticipante,
    ParticipanteInstrumento,
    ResultadoDimension,
)
from app.models.survey import Dimension
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
    elif rol in {"JEFE", "ADMINISTRADOR"}:
        # Solo las áreas de las empresas que el usuario creó.
        query_areas = (
            db.query(Area)
            .join(Organizacion, Organizacion.id == Area.organizacion_id)
            .options(joinedload(Area.organizacion))
            .filter(Organizacion.creada_por_id == actual.id)
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


# Instrumentos que no se califican (solo datos sociodemográficos): no se muestran sus "resultados"
_INSTRUMENTOS_SIN_CALIFICACION = {"FICHA_DATOS"}


def listar_encuestas_realizadas(db: Session, actual: Usuario) -> list[dict]:
    """Lista las encuestas (participaciones en una evaluación) con su avance y resultados.

    - SUPER_ADMINISTRADOR: ve las de todas las organizaciones.
    - EVALUADOR_SST: solo las de su organización.
    Se usa en la sección "Encuestas realizadas" de la página Reportes.

    Los resultados individuales son información confidencial (Resolución 2764 de 2022);
    por eso el endpoint solo está disponible para gestores (require_gestor).
    Las respuestas crudas cifradas NO se devuelven, solo el avance y los niveles calculados.
    """
    rol = actual.rol.codigo
    query = (
        db.query(EvaluacionParticipante)
        .join(Evaluacion, Evaluacion.id == EvaluacionParticipante.evaluacion_id)
        .options(
            joinedload(EvaluacionParticipante.evaluacion).joinedload(Evaluacion.organizacion),
            joinedload(EvaluacionParticipante.trabajador),
            joinedload(EvaluacionParticipante.instrumentos_asignados)
            .joinedload(ParticipanteInstrumento.instrumento)
            .joinedload(EvaluacionInstrumento.version),
        )
    )
    if rol == "EVALUADOR_SST":
        if not actual.organizacion_id:
            return []
        query = query.filter(Evaluacion.organizacion_id == actual.organizacion_id)
    elif rol != "SUPER_ADMINISTRADOR":
        raise AppError(403, "No tiene permisos para consultar encuestas.")

    # Las más recientes primero: primero las terminadas (fecha_fin), luego las que están en curso
    participantes = query.order_by(
        EvaluacionParticipante.fecha_fin.desc().nullslast(),
        Evaluacion.creado_en.desc(),
    ).all()

    encuestas = []
    for part in participantes:
        # Avance por instrumento, en el orden en que se responden (Ficha, Estrés, Extralaboral, Intralaboral)
        instrumentos = [
            {
                "codigo": pi.instrumento.version.codigo,
                "nombre": pi.instrumento.version.nombre,
                "estado": pi.estado,
            }
            for pi in sorted(part.instrumentos_asignados, key=lambda i: i.instrumento.orden)
        ]

        # Resultados calculados al finalizar la batería (tabulacion.tabular_participante)
        resultados = []
        filas = (
            db.query(ResultadoDimension)
            .options(joinedload(ResultadoDimension.dimension).joinedload(Dimension.version))
            .filter(ResultadoDimension.participante_id == part.id)
            .all()
        )
        for r in filas:
            codigo_instrumento = r.dimension.version.codigo
            if codigo_instrumento in _INSTRUMENTOS_SIN_CALIFICACION:
                continue
            resultados.append(
                {
                    "instrumento": codigo_instrumento,
                    "dimension": r.dimension.nombre,
                    "tipo": r.dimension.tipo or "DIMENSION",
                    "puntajeTransformado": r.puntaje_transformado,
                    "nivel": r.nivel,
                }
            )

        trabajador = part.trabajador
        evaluacion = part.evaluacion
        encuestas.append(
            {
                "participanteId": str(part.id),
                "evaluacionId": str(evaluacion.id),
                "evaluacionNombre": evaluacion.nombre,
                "evaluacionEstado": evaluacion.estado,
                "organizacionNombre": evaluacion.organizacion.nombre if evaluacion.organizacion else None,
                "trabajadorNombre": f"{trabajador.nombre} {trabajador.apellido}".strip(),
                # Los pacientes del enlace tienen un correo interno generado: no se muestra
                "trabajadorEmail": None if trabajador.es_invitado else trabajador.email,
                "viaEnlace": trabajador.es_invitado,
                "estado": part.estado,  # PENDIENTE / EN_PROGRESO / COMPLETADA
                "fechaInicio": part.fecha_inicio.isoformat() if part.fecha_inicio else None,
                "fechaFin": part.fecha_fin.isoformat() if part.fecha_fin else None,
                "instrumentos": instrumentos,
                "instrumentosCompletados": sum(1 for i in instrumentos if i["estado"] == "COMPLETADA"),
                "resultados": resultados,
            }
        )
    return encuestas
