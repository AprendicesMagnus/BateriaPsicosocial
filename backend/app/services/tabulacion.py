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
        )
        .filter(EvaluacionParticipante.id == participante.id)
        .one()
    )
    dimensiones = (
        db.query(Dimension)
        .options(joinedload(Dimension.preguntas), joinedload(Dimension.baremos))
        .filter(Dimension.version_id == participante.evaluacion.version_id)
        .all()
    )
    valores = {r.pregunta_id: int(descifrar_json(r.valor_cifrado)) for r in participante.respuestas}
    resultados = []
    db.query(ResultadoDimension).filter(ResultadoDimension.participante_id == participante.id).delete()
    for dimension in dimensiones:
        puntaje = 0
        minimo = 0
        maximo = 0
        for pregunta in dimension.preguntas:
            crudo = valores.get(pregunta.id)
            if crudo is None:
                continue
            valor = _valor_item(pregunta, crudo)
            puntaje += valor
            minimo += pregunta.valor_minimo
            maximo += pregunta.valor_maximo
        transformado = 0.0 if maximo == minimo else 100.0 * (puntaje - minimo) / (maximo - minimo)
        nivel = _clasificar(transformado, dimension)
        registro = ResultadoDimension(
            participante_id=participante.id,
            dimension_id=dimension.id,
            puntaje_bruto=float(puntaje),
            puntaje_transformado=round(transformado, 2),
            nivel=nivel,
        )
        db.add(registro)
        resultados.append(
            {
                "dimensionId": str(dimension.id),
                "dimension": dimension.nombre,
                "dominio": dimension.dominio,
                "puntajeBruto": registro.puntaje_bruto,
                "puntajeTransformado": registro.puntaje_transformado,
                "nivel": nivel,
            }
        )
    return resultados


def _valor_item(pregunta: Pregunta, crudo: int) -> int:
    if pregunta.inversa:
        return pregunta.valor_maximo + pregunta.valor_minimo - crudo
    return crudo


def _clasificar(puntaje: float, dimension: Dimension) -> str:
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
