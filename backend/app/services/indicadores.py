from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Organizacion, Area
from app.models.survey import Dimension
from app.models.user import Usuario

settings = get_settings()

def obtener_resumen_indicadores(db: Session, organizacion_id: UUID | None = None) -> dict:
    # 1. Conteo de organizaciones
    query_orgs = db.query(Organizacion)
    if organizacion_id:
        query_orgs = query_orgs.filter(Organizacion.id == organizacion_id)
    total_organizaciones = query_orgs.count()

    # 2. Conteo de evaluaciones por estado
    query_evals = db.query(Evaluacion)
    if organizacion_id:
        query_evals = query_evals.filter(Evaluacion.organizacion_id == organizacion_id)
    
    evaluaciones = query_evals.all()
    evaluaciones_por_estado = {
        "BORRADOR": 0,
        "EN_CURSO": 0,
        "FINALIZADA": 0
    }
    for e in evaluaciones:
        if e.estado in evaluaciones_por_estado:
            evaluaciones_por_estado[e.estado] += 1

    # 3. Total participantes y porcentaje de participación (completados vs asignados)
    query_parts = db.query(EvaluacionParticipante).join(Evaluacion, Evaluacion.id == EvaluacionParticipante.evaluacion_id)
    if organizacion_id:
        query_parts = query_parts.filter(Evaluacion.organizacion_id == organizacion_id)
    
    participantes = query_parts.all()
    total_asignados = len(participantes)
    total_completados = sum(1 for p in participantes if p.estado == "COMPLETADA")
    tasa_participacion = round((total_completados / total_asignados * 100.0), 1) if total_asignados > 0 else 0.0

    # 4. Distribución de niveles de riesgo (respetando anonimato)
    distribucion_riesgo = {"SIN_RIESGO": 0, "BAJO": 0, "MEDIO": 0, "ALTO": 0, "MUY_ALTO": 0}
    anonimizado = False

    if total_completados < settings.min_grupo_anonimato:
        anonimizado = True
        # Se omite el desglose detallado de niveles de riesgo para proteger el anonimato
    else:
        query_res = db.query(ResultadoDimension).join(EvaluacionParticipante).join(Evaluacion)
        if organizacion_id:
            query_res = query_res.filter(Evaluacion.organizacion_id == organizacion_id)
        
        resultados = query_res.all()
        for r in resultados:
            if r.nivel in distribucion_riesgo:
                distribucion_riesgo[r.nivel] += 1

    return {
        "totalOrganizaciones": total_organizaciones,
        "totalEvaluaciones": len(evaluaciones),
        "evaluacionesPorEstado": evaluaciones_por_estado,
        "participacion": {
            "totalAsignados": total_asignados,
            "totalCompletados": total_completados,
            "tasaPorcentaje": tasa_participacion,
        },
        "distribucionRiesgo": distribucion_riesgo if not anonimizado else None,
        "anonimizado": anonimizado,
        "mensajeAnonimato": f"Requiere al menos {settings.min_grupo_anonimato} participantes completados para desglosar niveles de riesgo." if anonimizado else None
    }


def obtener_historico_indicadores(
    db: Session, organizacion_id: UUID | None = None, dimension_id: UUID | None = None
) -> dict:
    query = (
        db.query(ResultadoDimension)
        .join(EvaluacionParticipante, ResultadoDimension.participante_id == EvaluacionParticipante.id)
        .join(Evaluacion, EvaluacionParticipante.evaluacion_id == Evaluacion.id)
        .join(Dimension, ResultadoDimension.dimension_id == Dimension.id)
        .options(
            joinedload(ResultadoDimension.dimension),
            joinedload(ResultadoDimension.participante).joinedload(EvaluacionParticipante.evaluacion),
        )
    )

    if organizacion_id:
        query = query.filter(Evaluacion.organizacion_id == organizacion_id)

    if dimension_id:
        query = query.filter(ResultadoDimension.dimension_id == dimension_id)

    resultados = query.all()

    # Agrupar resultados por evaluacion_id
    evals_map = {}
    dim_nombre = None

    for r in resultados:
        eval_obj = r.participante.evaluacion
        e_id = str(eval_obj.id)
        if dimension_id and not dim_nombre:
            dim_nombre = r.dimension.nombre

        if e_id not in evals_map:
            evals_map[e_id] = {
                "evaluacionId": e_id,
                "nombreEvaluacion": eval_obj.nombre,
                "fecha": (eval_obj.fecha_fin or eval_obj.creado_en).isoformat(),
                "creadoEn": eval_obj.creado_en,
                "puntajes": [],
                "niveles": {"SIN_RIESGO": 0, "BAJO": 0, "MEDIO": 0, "ALTO": 0, "MUY_ALTO": 0},
            }

        evals_map[e_id]["puntajes"].append(r.puntaje_transformado)
        if r.nivel in evals_map[e_id]["niveles"]:
            evals_map[e_id]["niveles"][r.nivel] += 1

    # Ordenar evaluaciones cronológicamente
    evals_ordenadas = sorted(evals_map.values(), key=lambda x: x["creadoEn"])

    historico_salida = []
    for item in evals_ordenadas:
        pts = item["puntajes"]
        promedio = round(sum(pts) / len(pts), 2) if pts else 0.0
        historico_salida.append({
            "evaluacionId": item["evaluacionId"],
            "nombreEvaluacion": item["nombreEvaluacion"],
            "fecha": item["fecha"],
            "promedioPuntajeTransformado": promedio,
            "totalParticipantes": len(pts),
            "distribucionNiveles": item["niveles"],
        })

    return {
        "organizacionId": str(organizacion_id) if organizacion_id else None,
        "dimensionId": str(dimension_id) if dimension_id else None,
        "dimensionNombre": dim_nombre,
        "historico": historico_salida,
    }


def obtener_distribucion_por_categoria(
    db, organizacion_id=None
):
    """Devuelve la distribucion de niveles de riesgo por categoria (codigo de cuestionario).

    Respeta la regla de anonimato: si una categoria tiene menos de
    settings.min_grupo_anonimato participantes completados, devuelve null para esa categoria.
    """
    from sqlalchemy import func as _func
    from app.models.survey import CuestionarioVersion
    from app.models.evaluation import ResultadoDimension, EvaluacionParticipante, Evaluacion
    from app.models.survey import Dimension
    from app.core.config import get_settings as _get_settings
    _settings = _get_settings()

    # Agrupar ResultadoDimension por CuestionarioVersion.codigo y nivel
    query = (
        db.query(
            CuestionarioVersion.codigo,
            CuestionarioVersion.nombre,
            ResultadoDimension.nivel,
            _func.count(ResultadoDimension.id).label("conteo"),
        )
        .join(EvaluacionParticipante, ResultadoDimension.participante_id == EvaluacionParticipante.id)
        .join(Evaluacion, EvaluacionParticipante.evaluacion_id == Evaluacion.id)
        .join(Dimension, ResultadoDimension.dimension_id == Dimension.id)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(EvaluacionParticipante.estado == "COMPLETADA")
    )

    if organizacion_id:
        query = query.filter(Evaluacion.organizacion_id == organizacion_id)

    filas = query.group_by(
        CuestionarioVersion.codigo, CuestionarioVersion.nombre, ResultadoDimension.nivel
    ).all()

    # Agrupar por categoria acumulando niveles
    categorias = {}
    for codigo, nombre, nivel, conteo in filas:
        if codigo not in categorias:
            categorias[codigo] = {
                "codigo": codigo,
                "nombre": nombre,
                "totalParticipantes": 0,
                "distribucion": {"SIN_RIESGO": 0, "BAJO": 0, "MEDIO": 0, "ALTO": 0, "MUY_ALTO": 0},
            }
        if nivel in categorias[codigo]["distribucion"]:
            categorias[codigo]["distribucion"][nivel] += conteo
            categorias[codigo]["totalParticipantes"] += conteo

    # Aplicar regla de anonimato por categoria
    resultado = {}
    for codigo, cat in categorias.items():
        if cat["totalParticipantes"] < _settings.min_grupo_anonimato:
            resultado[codigo] = {
                "codigo": codigo,
                "nombre": cat["nombre"],
                "distribucion": None,
                "anonimizado": True,
                "mensajeAnonimato": (
                    f"Requiere al menos {_settings.min_grupo_anonimato} participantes "
                    "completados para desglosar niveles de riesgo."
                ),
            }
        else:
            resultado[codigo] = {
                "codigo": codigo,
                "nombre": cat["nombre"],
                "distribucion": cat["distribucion"],
                "anonimizado": False,
                "mensajeAnonimato": None,
            }

    return {"categorias": resultado}
