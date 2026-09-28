import uuid
from sqlalchemy.orm import Session, joinedload

from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.survey import SeguimientoRecomendacion, Recomendacion, Dimension
from app.models.user import Usuario


def validar_permiso_seguimiento(actual: Usuario):
    if actual.rol.codigo not in {"ADMINISTRADOR", "EVALUADOR_SST"}:
        raise AppError(403, "No tiene permisos para gestionar el plan de acción / seguimiento de recomendaciones.")


def listar_seguimientos(db: Session, organizacion_id: uuid.UUID | None, actual: Usuario) -> list[dict]:
    validar_permiso_seguimiento(actual)

    if actual.rol.codigo == "EVALUADOR_SST":
        organizacion_id = actual.organizacion_id

    query = (
        db.query(SeguimientoRecomendacion)
        .options(
            joinedload(SeguimientoRecomendacion.recomendacion).joinedload(Recomendacion.dimension)
        )
    )

    if organizacion_id:
        query = query.filter(SeguimientoRecomendacion.organizacion_id == organizacion_id)

    registros = query.all()

    return [
        {
            "id": str(s.id),
            "organizacionId": str(s.organizacion_id),
            "recomendacionId": str(s.recomendacion_id),
            "estado": s.estado,
            "responsable": s.responsable,
            "fechaEstado": s.fecha_estado.isoformat() if s.fecha_estado else None,
            "notas": s.notas,
            "creadoEn": s.creado_en.isoformat() if s.creado_en else None,
            "recomendacion": {
                "id": str(s.recomendacion.id),
                "titulo": s.recomendacion.titulo,
                "descripcion": s.recomendacion.descripcion,
                "nivel": s.recomendacion.nivel,
                "dimension": s.recomendacion.dimension.nombre if s.recomendacion and s.recomendacion.dimension else None,
            } if s.recomendacion else None,
        }
        for s in registros
    ]


def crear_o_actualizar_estado(
    db: Session,
    organizacion_id: uuid.UUID,
    recomendacion_id: uuid.UUID,
    estado: str,
    actual: Usuario,
    responsable: str | None = None,
    notas: str | None = None,
) -> dict:
    validar_permiso_seguimiento(actual)

    if actual.rol.codigo == "EVALUADOR_SST":
        organizacion_id = actual.organizacion_id

    if not organizacion_id:
        raise AppError(400, "Debe especificar la organización.")

    estados_validos = {"PENDIENTE", "EN_PROGRESO", "IMPLEMENTADA"}
    if estado not in estados_validos:
        raise AppError(400, f"Estado '{estado}' no válido. Opciones permitidas: PENDIENTE, EN_PROGRESO, IMPLEMENTADA.")

    rec = db.query(Recomendacion).filter(Recomendacion.id == recomendacion_id).first()
    if not rec:
        raise AppError(404, "Recomendación no encontrada.")

    registro = (
        db.query(SeguimientoRecomendacion)
        .filter(
            SeguimientoRecomendacion.organizacion_id == organizacion_id,
            SeguimientoRecomendacion.recomendacion_id == recomendacion_id,
        )
        .first()
    )

    ahora = utcnow()
    if registro:
        registro.estado = estado
        registro.fecha_estado = ahora
        if responsable is not None:
            registro.responsable = responsable
        if notas is not None:
            registro.notas = notas
    else:
        registro = SeguimientoRecomendacion(
            organizacion_id=organizacion_id,
            recomendacion_id=recomendacion_id,
            estado=estado,
            responsable=responsable,
            fecha_estado=ahora,
            notas=notas,
            creado_en=ahora,
        )
        db.add(registro)

    db.commit()
    db.refresh(registro)

    return {
        "id": str(registro.id),
        "organizacionId": str(registro.organizacion_id),
        "recomendacionId": str(registro.recomendacion_id),
        "estado": registro.estado,
        "responsable": registro.responsable,
        "fechaEstado": registro.fecha_estado.isoformat(),
        "notas": registro.notas,
        "creadoEn": registro.creado_en.isoformat(),
    }
