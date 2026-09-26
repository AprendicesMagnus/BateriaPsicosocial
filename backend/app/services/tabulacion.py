from sqlalchemy.orm import Session, joinedload

from app.core.encryption import descifrar_json
from app.core.errors import AppError
from app.models.evaluation import EvaluacionParticipante, ResultadoDimension
from app.models.survey import Dimension, Pregunta


def tabular_participante(db: Session, participante: EvaluacionParticipante) -> list[dict]:
    participante = (
        db.query(EvaluacionParticipante)
        .options(
            joinedload(EvaluacionParticipante.respuestas),
            joinedload(EvaluacionParticipante.evaluacion),
            joinedload(EvaluacionParticipante.instrumentos_asignados),
        )
        .filter(EvaluacionParticipante.id == participante.id)
        .one()
    )
    if participante.instrumentos_asignados:
        version_ids = [pi.instrumento.version_id for pi in participante.instrumentos_asignados]
        dimensiones = (
            db.query(Dimension)
            .options(joinedload(Dimension.preguntas), joinedload(Dimension.baremos))
            .filter(Dimension.version_id.in_(version_ids))
            .all()
        )
    else:
        dimensiones = (
            db.query(Dimension)
            .options(joinedload(Dimension.preguntas), joinedload(Dimension.baremos))
            .filter(Dimension.version_id == participante.evaluacion.version_id)
            .all()
        )
    valores = {}
    for r in participante.respuestas:
        val_desc = descifrar_json(r.valor_cifrado)
        try:
            valores[r.pregunta_id] = int(val_desc)
        except (ValueError, TypeError):
            continue
    resultados = []
    db.query(ResultadoDimension).filter(ResultadoDimension.participante_id == participante.id).delete()

    brutos_dimension = {}
    registros_base = []
    for dimension in dimensiones:
        tipo = dimension.tipo or "DIMENSION"
        if tipo != "DIMENSION":
            continue
        puntaje = 0
        minimo = 0
        maximo = 0
        respondidas = 0
        for pregunta in dimension.preguntas:
            crudo = valores.get(pregunta.id)
            if crudo is None:
                continue
            valor = _valor_item(pregunta, crudo)
            puntaje += valor
            minimo += pregunta.valor_minimo
            maximo += pregunta.valor_maximo
            respondidas += 1
        transformado = _transformar(puntaje, minimo, maximo, dimension, respondidas)
        nivel = _clasificar(transformado, dimension)
        registro = ResultadoDimension(
            participante_id=participante.id,
            dimension_id=dimension.id,
            puntaje_bruto=float(puntaje),
            puntaje_transformado=transformado,
            nivel=nivel,
        )
        brutos_dimension[dimension.id] = float(puntaje)
        registros_base.append((dimension, registro))

    brutos_dominio = {}
    for dimension in dimensiones:
        if (dimension.tipo or "DIMENSION") != "DOMINIO":
            continue
        hijos = [
            d
            for d in dimensiones
            if (d.tipo or "DIMENSION") == "DIMENSION" and d.dominio == dimension.nombre and d.version_id == dimension.version_id
        ]
        puntaje = sum(brutos_dimension.get(h.id, 0.0) for h in hijos)
        transformado = _transformar(puntaje, 0, 0, dimension, len(hijos))
        nivel = _clasificar(transformado, dimension)
        registro = ResultadoDimension(
            participante_id=participante.id,
            dimension_id=dimension.id,
            puntaje_bruto=float(puntaje),
            puntaje_transformado=transformado,
            nivel=nivel,
        )
        brutos_dominio[dimension.id] = float(puntaje)
        registros_base.append((dimension, registro))

    for dimension in dimensiones:
        if (dimension.tipo or "DIMENSION") != "TOTAL":
            continue
        hermanos = [d for d in dimensiones if (d.tipo or "DIMENSION") == "DOMINIO" and d.version_id == dimension.version_id]
        if hermanos:
            puntaje = sum(brutos_dominio.get(h.id, 0.0) for h in hermanos)
        else:
            puntaje = sum(brutos_dimension.values())
        transformado = _transformar(puntaje, 0, 0, dimension, 1)
        nivel = _clasificar(transformado, dimension)
        registro = ResultadoDimension(
            participante_id=participante.id,
            dimension_id=dimension.id,
            puntaje_bruto=float(puntaje),
            puntaje_transformado=transformado,
            nivel=nivel,
        )
        registros_base.append((dimension, registro))

    for dimension, registro in registros_base:
        db.add(registro)
        resultados.append(
            {
                "dimensionId": str(dimension.id),
                "dimension": dimension.nombre,
                "dominio": dimension.dominio,
                "tipo": dimension.tipo or "DIMENSION",
                "puntajeBruto": registro.puntaje_bruto,
                "puntajeTransformado": registro.puntaje_transformado,
                "nivel": registro.nivel,
            }
        )
    return resultados


def _a_escala_0_4(pregunta: Pregunta, crudo: int) -> int:
    """Convierte la respuesta almacenada a la escala oficial 0-4 (Nunca..Siempre de frecuencia)."""
    if pregunta.valor_minimo == 0 and pregunta.valor_maximo == 4:
        if crudo > 4:
            crudo = crudo - 1
        crudo = max(0, min(4, crudo))
        if pregunta.inversa:
            return 4 - crudo
        return crudo
    if pregunta.inversa:
        return pregunta.valor_maximo + pregunta.valor_minimo - crudo
    return crudo


def _valor_item(pregunta: Pregunta, crudo: int) -> int:
    return _a_escala_0_4(pregunta, crudo)


def _redondear_manual(valor: float) -> float:
    return round(valor + 1e-12, 1)


def _transformar(puntaje: float, minimo: float, maximo: float, dimension: Dimension, n_respondidas: int) -> float:
    factor = dimension.factor_transformacion
    if factor:
        if factor == 0:
            return 0.0
        return _redondear_manual(100.0 * float(puntaje) / float(factor))
    if maximo == minimo:
        return 0.0
    return round(100.0 * (puntaje - minimo) / (maximo - minimo), 2)


def _clasificar(puntaje: float, dimension: Dimension) -> str:
    if not dimension.baremos:
        if puntaje < 20.0:
            return "SIN_RIESGO"
        elif puntaje < 40.0:
            return "BAJO"
        elif puntaje < 60.0:
            return "MEDIO"
        elif puntaje < 80.0:
            return "ALTO"
        else:
            return "MUY_ALTO"
    for baremo in sorted(dimension.baremos, key=lambda b: b.orden):
        if baremo.minimo <= puntaje <= baremo.maximo:
            return baremo.nivel
    return "SIN_CLASIFICAR"


def resultados_evaluacion(db: Session, evaluacion_id, actual) -> list[dict]:
    from app.services.evaluaciones import obtener_evaluacion

    evaluacion = obtener_evaluacion(db, evaluacion_id, actual)
    participantes = (
        db.query(EvaluacionParticipante)
        .options(joinedload(EvaluacionParticipante.resultados).joinedload(ResultadoDimension.dimension))
        .filter(EvaluacionParticipante.evaluacion_id == evaluacion_id)
        .all()
    )
    salida = []
    for participante in participantes:
        if actual.rol.codigo == "TRABAJADOR" and participante.trabajador_id != actual.id:
            continue
        if not participante.resultados:
            continue
        item = {
            "participanteId": str(participante.id),
            "estado": participante.estado,
            "resultados": [
                {
                    "dimension": r.dimension.nombre,
                    "dominio": r.dimension.dominio,
                    "tipo": r.dimension.tipo or "DIMENSION",
                    "puntajeTransformado": r.puntaje_transformado,
                    "nivel": r.nivel,
                }
                for r in participante.resultados
            ],
        }
        if actual.rol.codigo != "TRABAJADOR":
            item["trabajadorId"] = str(participante.trabajador_id)
        salida.append(item)
    if not salida:
        raise AppError(400, "Los resultados aún no pueden ser consultados.")
    return salida
