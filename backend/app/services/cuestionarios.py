from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.models.evaluation import Respuesta
from app.models.survey import Baremo, CuestionarioVersion, Dimension, Pregunta


def listar_cuestionarios(db: Session) -> list[dict]:
    versiones = (
        db.query(CuestionarioVersion)
        .options(joinedload(CuestionarioVersion.dimensiones).joinedload(Dimension.preguntas))
        .order_by(CuestionarioVersion.codigo.asc(), CuestionarioVersion.numero_version.desc())
        .all()
    )
    return [_serializar_version(v, incluir_preguntas=False) for v in versiones]


def obtener_cuestionario(db: Session, version_id) -> dict:
    version = (
        db.query(CuestionarioVersion)
        .options(
            joinedload(CuestionarioVersion.dimensiones).joinedload(Dimension.preguntas),
            joinedload(CuestionarioVersion.dimensiones).joinedload(Dimension.baremos),
        )
        .filter(CuestionarioVersion.id == version_id)
        .first()
    )
    if version is None:
        raise AppError(404, "Cuestionario no encontrado.")
    return _serializar_version(version, incluir_preguntas=True)


def crear_cuestionario(db: Session, data) -> dict:
    ultima = (
        db.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == data.codigo)
        .order_by(CuestionarioVersion.numero_version.desc())
        .first()
    )
    numero = 1 if ultima is None else ultima.numero_version + 1
    if ultima:
        ultima.vigente = False

    version = CuestionarioVersion(
        codigo=data.codigo,
        nombre=data.nombre,
        numero_version=numero,
        descripcion=data.descripcion,
        vigente=True,
    )
    db.add(version)
    db.flush()

    dimensiones_por_codigo: dict[str, Dimension] = {}
    for dim_data in data.dimensiones:
        dimension = Dimension(
            version_id=version.id,
            codigo=dim_data.codigo,
            nombre=dim_data.nombre,
            dominio=dim_data.dominio,
            orden=dim_data.orden,
        )
        db.add(dimension)
        db.flush()
        dimensiones_por_codigo[dimension.codigo] = dimension
        for pregunta_data in dim_data.preguntas:
            db.add(
                Pregunta(
                    dimension_id=dimension.id,
                    codigo=pregunta_data.codigo,
                    enunciado=pregunta_data.enunciado,
                    orden=pregunta_data.orden,
                    inversa=pregunta_data.inversa,
                    valor_minimo=pregunta_data.valorMinimo,
                    valor_maximo=pregunta_data.valorMaximo,
                )
            )

    for baremo_data in data.baremos:
        dimension = dimensiones_por_codigo.get(baremo_data.dimensionCodigo)
        if dimension is None:
            raise AppError(400, f"No existe la dimensión {baremo_data.dimensionCodigo} en esta versión.")
        db.add(
            Baremo(
                dimension_id=dimension.id,
                nivel=baremo_data.nivel,
                minimo=baremo_data.minimo,
                maximo=baremo_data.maximo,
                orden=baremo_data.orden,
            )
        )
    db.commit()
    return obtener_cuestionario(db, version.id)


def actualizar_pregunta(db: Session, pregunta_id, enunciado: str | None, inversa: bool | None) -> dict:
    pregunta = db.query(Pregunta).filter(Pregunta.id == pregunta_id).first()
    if pregunta is None:
        raise AppError(404, "Pregunta no encontrada.")
    if db.query(Respuesta).filter(Respuesta.pregunta_id == pregunta.id).first():
        raise AppError(
            400,
            "No se pueden modificar preguntas con respuestas asociadas. Cree una nueva versión del cuestionario.",
        )
    if enunciado is not None:
        pregunta.enunciado = enunciado
    if inversa is not None:
        pregunta.inversa = inversa
    db.commit()
    return {"id": str(pregunta.id)}


def eliminar_pregunta(db: Session, pregunta_id) -> dict:
    pregunta = db.query(Pregunta).filter(Pregunta.id == pregunta_id).first()
    if pregunta is None:
        raise AppError(404, "Pregunta no encontrada.")
    if db.query(Respuesta).filter(Respuesta.pregunta_id == pregunta.id).first():
        raise AppError(400, "No se pueden eliminar preguntas con respuestas asociadas a evaluaciones existentes.")
    db.delete(pregunta)
    db.commit()
    return {"message": "Pregunta eliminada."}


def version_vigente(db: Session) -> CuestionarioVersion:
    version = db.query(CuestionarioVersion).filter(CuestionarioVersion.vigente.is_(True)).first()
    if version is None:
        raise AppError(400, "No hay un cuestionario vigente configurado.")
    return version


def _serializar_version(version: CuestionarioVersion, incluir_preguntas: bool) -> dict:
    dimensiones = []
    for dimension in sorted(version.dimensiones, key=lambda d: d.orden):
        item = {
            "id": str(dimension.id),
            "codigo": dimension.codigo,
            "nombre": dimension.nombre,
            "dominio": dimension.dominio,
            "orden": dimension.orden,
        }
        if incluir_preguntas:
            item["preguntas"] = [
                {
                    "id": str(p.id),
                    "codigo": p.codigo,
                    "enunciado": p.enunciado,
                    "orden": p.orden,
                    "inversa": p.inversa,
                    "valorMinimo": p.valor_minimo,
                    "valorMaximo": p.valor_maximo,
                }
                for p in sorted(dimension.preguntas, key=lambda p: p.orden)
            ]
            item["baremos"] = [
                {
                    "nivel": b.nivel,
                    "minimo": b.minimo,
                    "maximo": b.maximo,
                    "orden": b.orden,
                }
                for b in sorted(dimension.baremos, key=lambda b: b.orden)
            ]
        dimensiones.append(item)
    return {
        "id": str(version.id),
        "codigo": version.codigo,
        "nombre": version.nombre,
        "numeroVersion": version.numero_version,
        "descripcion": version.descripcion,
        "vigente": version.vigente,
        "dimensiones": dimensiones,
    }
