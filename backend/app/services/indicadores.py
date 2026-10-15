from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case, func

from app.core.config import get_settings
from app.core.encryption import descifrar_json
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Respuesta, ResultadoDimension
from app.models.organization import Organizacion, Area
from app.models.survey import CuestionarioVersion, Dimension, Pregunta, Recomendacion, SeguimientoRecomendacion
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
                "participantes": set(),
                "niveles": {"SIN_RIESGO": 0, "BAJO": 0, "MEDIO": 0, "ALTO": 0, "MUY_ALTO": 0},
            }

        evals_map[e_id]["puntajes"].append(r.puntaje_transformado)
        evals_map[e_id]["participantes"].add(r.participante_id)
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
            "totalParticipantes": len(item["participantes"]),
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


ORDEN_NIVELES = ["SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"]
NOMBRE_SIN_AREA = "Sin área asignada"


def _resumir_celda(distribucion: dict[str, int], minimo: int) -> dict:
    total = sum(distribucion.values())
    if total < minimo:
        return {"anonimizado": True}
    predominante = max(
        ORDEN_NIVELES,
        key=lambda nivel: (distribucion[nivel], ORDEN_NIVELES.index(nivel)),
    )
    riesgo_alto = distribucion["ALTO"] + distribucion["MUY_ALTO"]
    return {
        "anonimizado": False,
        "total": total,
        "nivel": predominante,
        "porcentajeAltoMuyAlto": round(riesgo_alto * 100 / total, 1),
        "distribucion": distribucion,
    }


def obtener_mapa_calor(
    db: Session,
    organizacion_id: UUID | None = None,
    codigo: str | None = None,
) -> dict:
    """Mapa de calor area x dimension para un cuestionario.

    Cada celda resume los niveles de riesgo de los participantes COMPLETADOS del area.
    Si la celda tiene menos de settings.min_grupo_anonimato participantes no se expone
    ningun dato de ella. En empates gana el nivel de mayor riesgo.
    """
    minimo = get_settings().min_grupo_anonimato

    consulta = (
        db.query(
            CuestionarioVersion.codigo,
            CuestionarioVersion.nombre,
            Dimension.codigo,
            Dimension.nombre,
            Dimension.dominio,
            Dimension.orden,
            Usuario.area_id,
            Area.nombre,
            ResultadoDimension.nivel,
            func.count(ResultadoDimension.id),
        )
        .select_from(ResultadoDimension)
        .join(EvaluacionParticipante, ResultadoDimension.participante_id == EvaluacionParticipante.id)
        .join(Evaluacion, EvaluacionParticipante.evaluacion_id == Evaluacion.id)
        .join(Usuario, EvaluacionParticipante.trabajador_id == Usuario.id)
        .outerjoin(Area, Usuario.area_id == Area.id)
        .join(Dimension, ResultadoDimension.dimension_id == Dimension.id)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(EvaluacionParticipante.estado == "COMPLETADA")
    )
    if organizacion_id:
        consulta = consulta.filter(Evaluacion.organizacion_id == organizacion_id)

    filas = consulta.group_by(
        CuestionarioVersion.codigo,
        CuestionarioVersion.nombre,
        Dimension.codigo,
        Dimension.nombre,
        Dimension.dominio,
        Dimension.orden,
        Usuario.area_id,
        Area.nombre,
        ResultadoDimension.nivel,
    ).all()

    categorias: dict[str, str] = {}
    for cod_cuestionario, nombre_cuestionario, *_ in filas:
        categorias.setdefault(cod_cuestionario, nombre_cuestionario)

    if not categorias:
        return {"categorias": [], "codigo": None, "dimensiones": [], "areas": [], "minimoAnonimato": minimo}

    seleccionado = codigo if codigo in categorias else sorted(categorias)[0]

    dimensiones: dict[str, dict] = {}
    areas: dict = {}
    for cod_cuestionario, _nombre, cod_dim, nombre_dim, dominio, orden, area_id, nombre_area, nivel, conteo in filas:
        if cod_cuestionario != seleccionado or nivel not in ORDEN_NIVELES:
            continue
        dimensiones.setdefault(
            cod_dim,
            {"codigo": cod_dim, "nombre": nombre_dim, "dominio": dominio, "orden": orden},
        )
        area = areas.setdefault(
            area_id,
            {
                "id": str(area_id) if area_id else None,
                "nombre": nombre_area or NOMBRE_SIN_AREA,
                "distribuciones": {},
            },
        )
        distribucion = area["distribuciones"].setdefault(cod_dim, {n: 0 for n in ORDEN_NIVELES})
        distribucion[nivel] += conteo

    areas_salida = [
        {
            "id": area["id"],
            "nombre": area["nombre"],
            "celdas": {
                cod_dim: _resumir_celda(distribucion, minimo)
                for cod_dim, distribucion in area["distribuciones"].items()
            },
        }
        for area in sorted(areas.values(), key=lambda a: (a["id"] is None, a["nombre"].lower()))
    ]

    return {
        "categorias": [{"codigo": c, "nombre": n} for c, n in sorted(categorias.items())],
        "codigo": seleccionado,
        "dimensiones": sorted(dimensiones.values(), key=lambda d: d["orden"]),
        "areas": areas_salida,
        "minimoAnonimato": minimo,
    }


NIVELES_PRIORIZABLES = ("MUY_ALTO", "ALTO")


def obtener_priorizacion(
    db: Session,
    organizacion_id: UUID | None = None,
    limite: int = 10,
) -> dict:
    """Ranking de dimensiones con mayor riesgo y sus recomendaciones.

    indice = (2 * personas en MUY_ALTO + personas en ALTO) / participantes, entre 0 y 2.
    Las dimensiones con menos de settings.min_grupo_anonimato participantes no se listan
    y solo se informa cuantas quedaron ocultas.
    """
    minimo = get_settings().min_grupo_anonimato

    consulta = (
        db.query(
            Dimension.id,
            Dimension.nombre,
            Dimension.dominio,
            CuestionarioVersion.nombre,
            ResultadoDimension.nivel,
            func.count(ResultadoDimension.id),
        )
        .select_from(ResultadoDimension)
        .join(EvaluacionParticipante, ResultadoDimension.participante_id == EvaluacionParticipante.id)
        .join(Evaluacion, EvaluacionParticipante.evaluacion_id == Evaluacion.id)
        .join(Dimension, ResultadoDimension.dimension_id == Dimension.id)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(EvaluacionParticipante.estado == "COMPLETADA")
    )
    if organizacion_id:
        consulta = consulta.filter(Evaluacion.organizacion_id == organizacion_id)

    filas = consulta.group_by(
        Dimension.id,
        Dimension.nombre,
        Dimension.dominio,
        CuestionarioVersion.nombre,
        ResultadoDimension.nivel,
    ).all()

    dimensiones: dict = {}
    for dim_id, nombre, dominio, cuestionario, nivel, conteo in filas:
        dimension = dimensiones.setdefault(
            dim_id,
            {
                "id": dim_id,
                "nombre": nombre,
                "dominio": dominio,
                "cuestionario": cuestionario,
                "distribucion": {n: 0 for n in ORDEN_NIVELES},
            },
        )
        if nivel in dimension["distribucion"]:
            dimension["distribucion"][nivel] += conteo

    ocultas = 0
    candidatas = []
    for dimension in dimensiones.values():
        distribucion = dimension["distribucion"]
        total = sum(distribucion.values())
        if total < minimo:
            ocultas += 1
            continue
        muy_alto = distribucion["MUY_ALTO"]
        alto = distribucion["ALTO"]
        if muy_alto + alto == 0:
            continue
        candidatas.append(
            {
                **dimension,
                "total": total,
                "indice": round((2 * muy_alto + alto) / total, 2),
                "porcentajeAltoMuyAlto": round((muy_alto + alto) * 100 / total, 1),
            }
        )

    candidatas.sort(key=lambda d: (-d["indice"], -d["distribucion"]["MUY_ALTO"], -d["total"], d["nombre"]))
    seleccionadas = candidatas[:limite]

    recomendaciones: dict = {}
    seguimientos: dict = {}
    if seleccionadas:
        consulta_recs = (
            db.query(Recomendacion)
            .filter(
                Recomendacion.dimension_id.in_([d["id"] for d in seleccionadas]),
                Recomendacion.nivel.in_(NIVELES_PRIORIZABLES),
            )
            .order_by(Recomendacion.prioridad)
        )
        for rec in consulta_recs.all():
            recomendaciones.setdefault(rec.dimension_id, []).append(rec)
        if organizacion_id:
            seguimientos = {
                s.recomendacion_id: s.estado
                for s in db.query(SeguimientoRecomendacion).filter(
                    SeguimientoRecomendacion.organizacion_id == organizacion_id
                )
            }

    return {
        "dimensiones": [
            {
                "id": str(d["id"]),
                "nombre": d["nombre"],
                "dominio": d["dominio"],
                "cuestionario": d["cuestionario"],
                "total": d["total"],
                "distribucion": d["distribucion"],
                "indice": d["indice"],
                "porcentajeAltoMuyAlto": d["porcentajeAltoMuyAlto"],
                "recomendaciones": [
                    {
                        "id": str(r.id),
                        "titulo": r.titulo,
                        "descripcion": r.descripcion,
                        "nivel": r.nivel,
                        "estadoSeguimiento": seguimientos.get(r.id),
                    }
                    for r in recomendaciones.get(d["id"], [])
                    if d["distribucion"][r.nivel] > 0
                ],
            }
            for d in seleccionadas
        ],
        "dimensionesOcultas": ocultas,
        "minimoAnonimato": minimo,
    }


def _grupo_texto(valor) -> str | None:
    texto = str(valor).strip()
    return texto or None


def _grupo_sexo(valor) -> str | None:
    texto = str(valor).strip().lower()
    return texto.capitalize() if texto else None


def _grupo_edad(valor) -> str | None:
    try:
        edad = date.today().year - int(valor)
    except (TypeError, ValueError):
        return None
    if edad < 30:
        return "Menos de 30 años"
    if edad < 40:
        return "30 a 39 años"
    if edad < 50:
        return "40 a 49 años"
    return "50 años o más"


def _grupo_antiguedad(valor) -> str | None:
    texto = str(valor).strip().lower()
    if not texto:
        return None
    if texto.startswith("menos"):
        return "Menos de 1 año"
    try:
        anios = int(texto)
    except ValueError:
        return None
    if anios < 1:
        return "Menos de 1 año"
    if anios < 5:
        return "1 a 4 años"
    if anios < 10:
        return "5 a 9 años"
    return "10 años o más"


# clave -> (etiqueta, codigo de pregunta de la ficha, funcion que asigna el grupo)
VARIABLES_GRUPO = {
    "sexo": ("Sexo", "F2", _grupo_sexo),
    "rango_edad": ("Rango de edad", "F3", _grupo_edad),
    "estado_civil": ("Estado civil", "F4", _grupo_texto),
    "nivel_estudios": ("Nivel de estudios", "F5", _grupo_texto),
    "estrato": ("Estrato socioeconómico", "F9", _grupo_texto),
    "tipo_cargo": ("Tipo de cargo", "F16", _grupo_texto),
    "antiguedad_empresa": ("Antigüedad en la empresa", "F14", _grupo_antiguedad),
    "tipo_contrato": ("Tipo de contrato", "F19", _grupo_texto),
    "tipo_salario": ("Tipo de salario", "F21", _grupo_texto),
}


def obtener_analisis_grupos(
    db: Session,
    organizacion_id: UUID | None = None,
    codigo: str | None = None,
    variable: str = "sexo",
) -> dict:
    """Riesgo por grupos de la ficha de datos generales para un cuestionario.

    Las respuestas de la ficha estan cifradas, por eso se descifran en memoria solo para
    agrupar; nunca se devuelven valores individuales. Los grupos con menos de
    settings.min_grupo_anonimato participantes no se listan y solo se cuentan.
    """
    if variable not in VARIABLES_GRUPO:
        raise AppError(400, "Variable de agrupación no válida.")
    _etiqueta, codigo_pregunta, agrupar = VARIABLES_GRUPO[variable]
    minimo = get_settings().min_grupo_anonimato
    variables = [{"clave": clave, "etiqueta": datos[0]} for clave, datos in VARIABLES_GRUPO.items()]

    consulta = (
        db.query(
            CuestionarioVersion.codigo,
            CuestionarioVersion.nombre,
            EvaluacionParticipante.id,
            func.count(ResultadoDimension.id),
            func.sum(case((ResultadoDimension.nivel.in_(NIVELES_PRIORIZABLES), 1), else_=0)),
            func.sum(ResultadoDimension.puntaje_transformado),
        )
        .select_from(ResultadoDimension)
        .join(EvaluacionParticipante, ResultadoDimension.participante_id == EvaluacionParticipante.id)
        .join(Evaluacion, EvaluacionParticipante.evaluacion_id == Evaluacion.id)
        .join(Dimension, ResultadoDimension.dimension_id == Dimension.id)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(EvaluacionParticipante.estado == "COMPLETADA")
    )
    if organizacion_id:
        consulta = consulta.filter(Evaluacion.organizacion_id == organizacion_id)

    filas = consulta.group_by(
        CuestionarioVersion.codigo,
        CuestionarioVersion.nombre,
        EvaluacionParticipante.id,
    ).all()

    categorias: dict[str, str] = {}
    for cod_cuestionario, nombre_cuestionario, *_ in filas:
        categorias.setdefault(cod_cuestionario, nombre_cuestionario)

    if not categorias:
        return {
            "categorias": [],
            "codigo": None,
            "variables": variables,
            "variable": variable,
            "grupos": [],
            "gruposOcultos": 0,
            "sinDato": 0,
            "minimoAnonimato": minimo,
        }

    seleccionado = codigo if codigo in categorias else sorted(categorias)[0]
    por_participante = {
        participante_id: (int(total), int(altos or 0), float(suma or 0.0))
        for cod_cuestionario, _nombre, participante_id, total, altos, suma in filas
        if cod_cuestionario == seleccionado
    }

    respuestas = (
        db.query(Respuesta.participante_id, Respuesta.valor_cifrado)
        .join(Pregunta, Respuesta.pregunta_id == Pregunta.id)
        .join(Dimension, Pregunta.dimension_id == Dimension.id)
        .join(CuestionarioVersion, Dimension.version_id == CuestionarioVersion.id)
        .filter(
            CuestionarioVersion.codigo == "FICHA_DATOS",
            Pregunta.codigo == codigo_pregunta,
            Respuesta.participante_id.in_(list(por_participante)),
        )
        .all()
    )

    acumulado: dict[str, dict] = {}
    con_dato: set = set()
    for participante_id, valor_cifrado in respuestas:
        try:
            nombre_grupo = agrupar(descifrar_json(valor_cifrado))
        except ValueError:
            continue
        if not nombre_grupo:
            continue
        resultados, altos, suma = por_participante[participante_id]
        grupo = acumulado.setdefault(
            nombre_grupo,
            {"participantes": 0, "resultados": 0, "altos": 0, "suma": 0.0},
        )
        grupo["participantes"] += 1
        grupo["resultados"] += resultados
        grupo["altos"] += altos
        grupo["suma"] += suma
        con_dato.add(participante_id)

    grupos = []
    ocultos = 0
    for nombre_grupo, grupo in acumulado.items():
        if grupo["participantes"] < minimo:
            ocultos += 1
            continue
        grupos.append(
            {
                "nombre": nombre_grupo,
                "participantes": grupo["participantes"],
                "porcentajeAltoMuyAlto": round(grupo["altos"] * 100 / grupo["resultados"], 1),
                "promedioPuntaje": round(grupo["suma"] / grupo["resultados"], 1),
            }
        )
    grupos.sort(key=lambda g: (-g["porcentajeAltoMuyAlto"], g["nombre"]))

    return {
        "categorias": [{"codigo": c, "nombre": n} for c, n in sorted(categorias.items())],
        "codigo": seleccionado,
        "variables": variables,
        "variable": variable,
        "grupos": grupos,
        "gruposOcultos": ocultos,
        "sinDato": len(por_participante) - len(con_dato),
        "minimoAnonimato": minimo,
    }



