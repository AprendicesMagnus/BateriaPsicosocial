import uuid
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Area
from app.models.survey import Dimension
from app.models.user import Usuario

settings = get_settings()


def analizar_riesgo_predictivo(
    db: Session,
    evaluacion_id: uuid.UUID,
    area_id: uuid.UUID | None = None,
) -> dict:
    evaluacion = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if evaluacion is None:
        raise AppError(404, "Evaluación no encontrada.")

    # 1. Obtener participantes completados
    query = (
        db.query(EvaluacionParticipante)
        .options(
            joinedload(EvaluacionParticipante.trabajador),
            joinedload(EvaluacionParticipante.resultados).joinedload(ResultadoDimension.dimension),
        )
        .filter(
            EvaluacionParticipante.evaluacion_id == evaluacion_id,
            EvaluacionParticipante.estado == "COMPLETADA",
        )
    )

    if area_id:
        query = query.join(Usuario, Usuario.id == EvaluacionParticipante.trabajador_id).filter(Usuario.area_id == area_id)

    participantes = query.all()
    num_participantes = len(participantes)

    # 2. Control de anonimato y muestra mínima
    if num_participantes < settings.min_grupo_anonimato:
        raise AppError(
            400,
            f"No se puede realizar el análisis predictivo. El grupo tiene {num_participantes} participante(s) completado(s), "
            f"lo cual es inferior al mínimo requerido para análisis analítico y anonimato ({settings.min_grupo_anonimato} personas).",
        )

    # 3. Obtener dimensiones del cuestionario
    dimensiones = (
        db.query(Dimension)
        .filter(Dimension.version_id == evaluacion.version_id)
        .order_by(Dimension.orden)
        .all()
    )

    if not dimensiones:
        raise AppError(400, "No se encontraron dimensiones asociadas al cuestionario de la evaluación.")

    dim_nombres = [d.nombre for d in dimensiones]
    dim_ids = [d.id for d in dimensiones]

    # 4. Construir matriz de características X (participantes x dimensiones)
    matrix = []
    for p in participantes:
        row = []
        for d_id in dim_ids:
            res_dim = next((r for r in p.resultados if r.dimension_id == d_id), None)
            val = res_dim.puntaje_transformado if res_dim else 0.0
            row.append(val)
        matrix.append(row)

    X = np.array(matrix, dtype=float)

    # 5. Análisis Descriptivo & Proyección de Incidencia de Riesgo
    incidencia_riesgo = []
    alertas_tempranas = []

    for i, dim in enumerate(dimensiones):
        scores = X[:, i]
        promedion = float(np.mean(scores))
        desviacion = float(np.std(scores))
        
        # Conteo de riesgo alto/muy alto
        conteo_critico = 0
        for p in participantes:
            res_dim = next((r for r in p.resultados if r.dimension_id == dim.id), None)
            if res_dim and res_dim.nivel in {"ALTO", "MUY_ALTO"}:
                conteo_critico += 1

        pct_critico = round((conteo_critico / num_participantes) * 100.0, 1)

        incidencia_riesgo.append({
            "dimensionId": str(dim.id),
            "dimension": dim.nombre,
            "dominio": dim.dominio,
            "promedioPuntaje": round(promedion, 2),
            "desviacionEstandar": round(desviacion, 2),
            "porcentajeRiesgoCritico": pct_critico,
        })

        # Alerta temprana: riesgo promedio >= 50 o > 30% en nivel alto
        if promedion >= 50.0 or pct_critico >= 30.0:
            alertas_tempranas.append({
                "dimension": dim.nombre,
                "nivelAlerta": "ALTA" if promedion >= 70.0 or pct_critico >= 50.0 else "MODERADA",
                "mensaje": f"La dimensión '{dim.nombre}' presenta un {pct_critico}% de población en nivel de riesgo Alto/Muy Alto y puntaje promedio de {round(promedion, 1)}.",
            })

    # 6. Agrupamiento K-Means (Clustering de perfiles de riesgo)
    unique_samples = len(np.unique(X, axis=0))
    n_clusters = min(3, max(1, unique_samples))
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)

    perfiles_clusters = []
    for c in range(n_clusters):
        idx = np.where(cluster_labels == c)[0]
        size = len(idx)
        if size == 0:
            continue
        cluster_scores = X[idx]
        cluster_means = np.mean(cluster_scores, axis=0)

        dim_resumen = {}
        for i, dim_nom in enumerate(dim_nombres):
            dim_resumen[dim_nom] = round(float(cluster_means[i]), 1)

        # Determinar etiqueta descriptiva del perfil
        prom_global_cluster = float(np.mean(cluster_means))
        if np.isnan(prom_global_cluster):
            prom_global_cluster = 0.0

        if prom_global_cluster >= 60.0:
            etiqueta = "Perfil de Alto Riesgo Psicosocial Global"
        elif prom_global_cluster >= 35.0:
            etiqueta = "Perfil de Riesgo Moderado"
        else:
            etiqueta = "Perfil de Bajo Riesgo / Saludable"

        perfiles_clusters.append({
            "clusterId": len(perfiles_clusters) + 1,
            "etiqueta": etiqueta,
            "numTrabajadores": size,
            "porcentajeGrupo": round((size / num_participantes) * 100.0, 1),
            "promedioGlobalPuntaje": round(prom_global_cluster, 1),
            "promedioPorDimension": dim_resumen,
        })

    return {
        "evaluacionId": str(evaluacion_id),
        "totalParticipantesAnalizados": num_participantes,
        "incidenciaRiesgoPorDimension": incidencia_riesgo,
        "alertasTempranas": alertas_tempranas,
        "perfilesClusterKMeans": perfiles_clusters,
        "notaMetodologica": (
            "Este modelo de análisis predictivo utiliza K-Means Clustering no supervisado sobre la matriz de "
            "resultados transformados. Al tratarse de un prototipo digital sin serie histórica longitudinal, "
            "las proyecciones corresponden a la detección no supervisada de perfiles de riesgo en la muestra actual."
        ),
        "estrategiaEntrenamiento": (
            "Entrenamiento al vuelo (Unsupervised K-Means clustering en tiempo de ejecución). "
            "Se eligió entrenamiento al vuelo para adaptar los clústeres al contexto real de la empresa evaluada."
        ),
    }
