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
    Respuesta,
    ResultadoDimension,
)
from app.core.encryption import descifrar_json
from app.models.survey import Dimension, Pregunta
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

# Roles que ven las encuestas de todas las organizaciones (require_gestor deja pasar a SUPER_ADMINISTRADOR)
_ROLES_VEN_TODAS = {"SUPER_ADMINISTRADOR", "ADMINISTRADOR"}


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
<<<<<<< HEAD
    elif rol not in _ROLES_VEN_TODAS:
=======
    elif rol != "SUPER_ADMINISTRADOR":
>>>>>>> fbda8549701f072fb0bd3d23034ef4eaf1b52ca9
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
                "trabajadorId": str(trabajador.id),
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


def respuestas_participante(db: Session, actual: Usuario, participante_id: uuid.UUID) -> dict:
    """Respuestas descifradas de un participante, agrupadas por instrumento.

    Mismo alcance que listar_encuestas_realizadas: el EVALUADOR_SST solo ve las de su organización.
    Se usa en la sección "Respuestas por usuario" de Reportes.jsx y se pide solo al abrir un usuario.
    """
    rol = actual.rol.codigo
    part = (
        db.query(EvaluacionParticipante)
        .options(
            joinedload(EvaluacionParticipante.evaluacion),
            joinedload(EvaluacionParticipante.trabajador),
            joinedload(EvaluacionParticipante.instrumentos_asignados)
            .joinedload(ParticipanteInstrumento.instrumento)
            .joinedload(EvaluacionInstrumento.version),
        )
        .filter(EvaluacionParticipante.id == participante_id)
        .first()
    )
    if part is None:
        raise AppError(404, "La encuesta no existe.")
    if rol == "EVALUADOR_SST":
        if part.evaluacion.organizacion_id != actual.organizacion_id:
            raise AppError(404, "La encuesta no existe.")
    elif rol not in _ROLES_VEN_TODAS:
        raise AppError(403, "No tiene permisos para consultar respuestas.")

    filas = (
        db.query(Respuesta)
        .options(joinedload(Respuesta.pregunta).joinedload(Pregunta.dimension).joinedload(Dimension.version))
        .filter(Respuesta.participante_id == part.id)
        .all()
    )
    # Respuestas agrupadas por la versión (instrumento) a la que pertenece cada pregunta
    por_version: dict[uuid.UUID, list] = {}
    for r in filas:
        por_version.setdefault(r.pregunta.dimension.version_id, []).append(r)

    # Primero los instrumentos asignados (en orden de respuesta); luego cualquier versión con
    # respuestas sin instrumento asignado (evaluaciones antiguas creadas solo con version_id)
    grupos = [
        (pi.instrumento.version, pi.estado)
        for pi in sorted(part.instrumentos_asignados, key=lambda i: i.instrumento.orden)
    ]
    asignadas = {version.id for version, _ in grupos}
    for version_id, respuestas in por_version.items():
        if version_id not in asignadas:
            grupos.append((respuestas[0].pregunta.dimension.version, None))

    instrumentos = []
    for version, estado in grupos:
        respuestas = sorted(por_version.get(version.id, []), key=lambda r: r.pregunta.orden)
        instrumentos.append(
            {
                "codigo": version.codigo,
                "nombre": version.nombre,
                "estado": estado,
                "respuestas": [
                    {
                        "orden": r.pregunta.orden,
                        "codigo": r.pregunta.codigo,
                        "enunciado": r.pregunta.enunciado,
                        "dimension": r.pregunta.dimension.nombre,
                        # Dominio de la dimensión: la vista Respuestas agrupa por dominio -> dimensión
                        "dominio": r.pregunta.dimension.dominio,
                        "tipo": r.pregunta.tipo_respuesta,
                        "valor": descifrar_json(r.valor_cifrado),
                    }
                    for r in respuestas
                ],
            }
        )

    trabajador = part.trabajador
    return {
        "participanteId": str(part.id),
        "trabajadorNombre": f"{trabajador.nombre} {trabajador.apellido}".strip(),
        "instrumentos": instrumentos,
    }
