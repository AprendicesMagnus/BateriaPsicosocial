import uuid
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension
from app.models.organization import Area
from app.models.survey import Dimension
from app.models.user import Usuario

settings = get_settings()


# --- Ayudantes del análisis (todo local con scikit-learn/numpy: sin servicios externos ni costo) ---
UMBRAL_DIFERENCIA = 5.0  # puntos por encima/debajo del promedio general para considerar un rasgo distintivo

RECOMENDACIONES_POR_TEMA = (
    ("liderazgo", "Fortalecer el acompañamiento y la comunicación de los jefes: capacitación en liderazgo y espacios regulares de retroalimentación."),
    ("control", "Aumentar la autonomía y la participación en las decisiones sobre cómo se organiza el trabajo, con capacitación para nuevas tareas."),
    ("demanda", "Revisar cargas de trabajo, ritmos, jornadas y pausas; redistribuir tareas donde haya sobrecarga."),
    ("recompensa", "Revisar el reconocimiento, la estabilidad y las oportunidades de desarrollo, y comunicar criterios claros."),
    ("extralaboral", "Ofrecer flexibilidad horaria y programas de bienestar que faciliten conciliar el trabajo con la vida personal."),
    ("estr", "Implementar pausas activas, formación en manejo del estrés y acceso a apoyo psicológico."),
)
RECOMENDACION_GENERAL = "Profundizar con el área responsable (mesas de trabajo o entrevistas) y definir un plan de intervención con seguimiento."


def _elegir_clusters(X_scaled: np.ndarray, muestras_unicas: int) -> tuple[int, float | None]:
    """Prueba de 2 a 4 grupos y se queda con el de mejor coeficiente de silueta (separación entre perfiles)."""
    n = X_scaled.shape[0]
    maximo = min(4, muestras_unicas, n - 1)
    if maximo < 2:
        return 1, None
    mejor_k, mejor_s = None, -1.0
    for k in range(2, maximo + 1):
        etiquetas = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_scaled)
        if len(set(etiquetas)) < 2:
            continue
        s = float(silhouette_score(X_scaled, etiquetas))
        if s > mejor_s + 1e-9:
            mejor_k, mejor_s = k, s
    return (mejor_k, mejor_s) if mejor_k else (1, None)


def _lectura_silueta(s: float | None) -> str:
    if s is None:
        return "Muestra insuficiente para separar perfiles."
    if s >= 0.5:
        return "Buena separación entre perfiles."
    if s >= 0.25:
        return "Separación aceptable entre perfiles."
    return "Separación débil: los perfiles se parecen bastante; interprétalos con cautela."


def _lista_factores(factores: list[dict]) -> str:
    textos = [f"{f['dimension']} ({f['diferencia']:+.1f} pts)" for f in factores]
    return ", ".join(textos[:-1]) + " y " + textos[-1] if len(textos) > 1 else textos[0]


def _describir_perfil(altos: list[dict], bajos: list[dict]) -> str:
    partes = []
    if altos:
        partes.append(f"Se distingue por puntajes de riesgo más altos en {_lista_factores(altos)}.")
    if bajos:
        partes.append(f"Sus puntos más favorables son {_lista_factores(bajos)}.")
    return " ".join(partes) or "Su perfil es similar al promedio general del grupo."


def _recomendacion_para(dominio: str | None, nombre: str) -> str:
    texto = f"{dominio or ''} {nombre}".lower()
    for clave, accion in RECOMENDACIONES_POR_TEMA:
        if clave in texto:
            return accion
    return RECOMENDACION_GENERAL


def _dimensiones_relacionadas(X: np.ndarray, nombres: list[str]) -> list[dict]:
    """Pares de dimensiones que suben o bajan juntas (solo con muestra suficiente para que sea confiable)."""
    if X.shape[0] < 8 or X.shape[1] < 2:
        return []
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.corrcoef(X, rowvar=False)
    pares = []
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            r = corr[i, j]
            if np.isnan(r) or abs(r) < 0.7:
                continue
            junto = r > 0
            pares.append({
                "dimensionA": nombres[i],
                "dimensionB": nombres[j],
                "correlacion": round(float(r), 2),
                "mensaje": (
                    f"'{nombres[i]}' y '{nombres[j]}' tienden a {'subir juntas' if junto else 'moverse en sentido contrario'} "
                    f"(r = {r:.2f}); conviene {'atenderlas en conjunto' if junto else 'revisar su relación'}."
                ),
            })
    pares.sort(key=lambda p: abs(p["correlacion"]), reverse=True)
    return pares[:5]


def _resumen_interpretativo(n: int, incidencia: list[dict], alertas: list[dict], k: int) -> str:
    promedio = float(np.mean([d["promedioPuntaje"] for d in incidencia])) if incidencia else 0.0
    nivel = "alto" if promedio >= 60 else "moderado" if promedio >= 35 else "bajo"
    texto = f"Se analizaron {n} cuestionario(s) completado(s). El puntaje de riesgo promedio es {promedio:.1f} pts (nivel {nivel})."
    criticas = sorted((d for d in incidencia if d["porcentajeRiesgoCritico"] > 0), key=lambda d: -d["porcentajeRiesgoCritico"])[:3]
    if criticas:
        lista = ", ".join(f"{d['dimension']} ({d['porcentajeRiesgoCritico']}%)" for d in criticas)
        texto += f" Las dimensiones con mayor proporción de personas en riesgo alto o muy alto son: {lista}."
    if alertas:
        altas = sum(1 for a in alertas if a["nivelAlerta"] == "ALTA")
        texto += f" Se generaron {len(alertas)} alerta(s) temprana(s), {altas} de nivel alto."
    else:
        texto += " No se generaron alertas tempranas."
    if k > 1:
        texto += f" El modelo encontró {k} perfiles de respuesta distintos dentro del grupo."
    return texto


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

    # 6. Agrupamiento K-Means: el número de perfiles (2 a 4) se elige solo, según qué tan separados queden
    unique_samples = len(np.unique(X, axis=0))
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    n_clusters, silueta = _elegir_clusters(X_scaled, unique_samples)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    medias_globales = np.mean(X, axis=0)

    perfiles_clusters = []
    for c in range(n_clusters):
        idx = np.where(cluster_labels == c)[0]
        size = len(idx)
        if size == 0:
            continue
        cluster_means = np.mean(X[idx], axis=0)

        dim_resumen = {nom: round(float(cluster_means[i]), 1) for i, nom in enumerate(dim_nombres)}

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

        # Qué distingue a este perfil del resto del grupo (explicación automática)
        altos, bajos = [], []
        if n_clusters > 1:
            diferencias = cluster_means - medias_globales
            for i in np.argsort(-diferencias):
                if diferencias[i] >= UMBRAL_DIFERENCIA and len(altos) < 3:
                    altos.append({"dimension": dim_nombres[i], "promedio": round(float(cluster_means[i]), 1), "diferencia": round(float(diferencias[i]), 1)})
            for i in np.argsort(diferencias):
                if diferencias[i] <= -UMBRAL_DIFERENCIA and len(bajos) < 2:
                    bajos.append({"dimension": dim_nombres[i], "promedio": round(float(cluster_means[i]), 1), "diferencia": round(float(diferencias[i]), 1)})

        perfiles_clusters.append({
            "etiqueta": etiqueta,
            "numTrabajadores": size,
            "porcentajeGrupo": round((size / num_participantes) * 100.0, 1),
            "promedioGlobalPuntaje": round(prom_global_cluster, 1),
            "promedioPorDimension": dim_resumen,
            "factoresMasAltos": altos,
            "factoresMasBajos": bajos,
            "descripcion": _describir_perfil(altos, bajos),
        })

    # Del perfil de mayor riesgo al de menor
    perfiles_clusters.sort(key=lambda p: -p["promedioGlobalPuntaje"])
    for orden, perfil in enumerate(perfiles_clusters, start=1):
        perfil["clusterId"] = orden

    # 7. Lectura automática: resumen, recomendaciones orientativas y dimensiones relacionadas
    por_dimension = {d["dimension"]: d for d in incidencia_riesgo}
    recomendaciones = []
    for alerta in sorted(alertas_tempranas, key=lambda a: (a["nivelAlerta"] != "ALTA", -por_dimension[a["dimension"]]["porcentajeRiesgoCritico"]))[:3]:
        info = por_dimension[alerta["dimension"]]
        recomendaciones.append({
            "dimension": alerta["dimension"],
            "nivelAlerta": alerta["nivelAlerta"],
            "accion": _recomendacion_para(info.get("dominio"), alerta["dimension"]),
        })

    return {
        "evaluacionId": str(evaluacion_id),
        "totalParticipantesAnalizados": num_participantes,
        "incidenciaRiesgoPorDimension": incidencia_riesgo,
        "alertasTempranas": alertas_tempranas,
        "perfilesClusterKMeans": perfiles_clusters,
        "resumenInterpretativo": _resumen_interpretativo(num_participantes, incidencia_riesgo, alertas_tempranas, n_clusters),
        "recomendacionesOrientativas": recomendaciones,
        "dimensionesRelacionadas": _dimensiones_relacionadas(X, dim_nombres),
        "calidadAgrupacion": {
            "perfilesElegidos": n_clusters,
            "silhouette": round(silueta, 2) if silueta is not None else None,
            "lectura": _lectura_silueta(silueta),
        },
        "notaMetodologica": (
            "Este modelo utiliza K-Means Clustering no supervisado sobre la matriz de resultados transformados. "
            "El número de perfiles (de 2 a 4) se elige automáticamente con el coeficiente de silueta. "
            "Al tratarse de un prototipo sin serie histórica longitudinal, los resultados describen la muestra actual "
            "y no constituyen un diagnóstico clínico. Las recomendaciones son orientativas y requieren el criterio del profesional SST."
        ),
        "estrategiaEntrenamiento": (
            "Entrenamiento al vuelo (K-Means no supervisado en tiempo de ejecución, con scikit-learn en el propio servidor: "
            "sin servicios externos y sin enviar datos fuera del sistema). Se adapta a cada empresa evaluada."
        ),
    }


def aplicar_anonimato_perfiles(resultado: dict, minimo: int | None = None) -> dict:
    if minimo is None:
        minimo = settings.min_grupo_anonimato
    res = dict(resultado)
    perfiles = res.get("perfilesClusterKMeans", []) or []
    visibles = [p for p in perfiles if p.get("numTrabajadores", 0) >= minimo]
    res["perfilesClusterKMeans"] = visibles
    res["perfilesOmitidos"] = len(perfiles) - len(visibles)
    res["minimoAnonimato"] = minimo
    return res

