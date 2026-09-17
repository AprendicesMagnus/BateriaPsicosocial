from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Organizacion, Area
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
