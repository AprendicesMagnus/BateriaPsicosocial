from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.plan import PlanBateria


def _publico(plan: PlanBateria) -> dict:
    return {
        "id": str(plan.id),
        "nombre": plan.nombre,
        "cantidadMin": plan.cantidad_min,
        "cantidadMax": plan.cantidad_max,
        "precioUnitario": plan.precio_unitario,
        "activo": plan.activo,
    }


def _validar_rango(minimo: int, maximo: int | None) -> None:
    if maximo is not None and maximo < minimo:
        raise AppError(400, "La cantidad máxima no puede ser menor que la mínima.")


def listar_planes(db: Session, solo_activos: bool) -> list[dict]:
    query = db.query(PlanBateria)
    if solo_activos:
        query = query.filter(PlanBateria.activo.is_(True))
    return [_publico(p) for p in query.order_by(PlanBateria.cantidad_min.asc()).all()]


def crear_plan(db: Session, data) -> dict:
    _validar_rango(data.cantidadMin, data.cantidadMax)
    plan = PlanBateria(
        nombre=data.nombre.strip(),
        cantidad_min=data.cantidadMin,
        cantidad_max=data.cantidadMax,
        precio_unitario=data.precioUnitario,
        activo=data.activo,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _publico(plan)


def _obtener(db: Session, plan_id) -> PlanBateria:
    plan = db.query(PlanBateria).filter(PlanBateria.id == plan_id).first()
    if plan is None:
        raise AppError(404, "Plan no encontrado.")
    return plan


def actualizar_plan(db: Session, plan_id, data) -> dict:
    plan = _obtener(db, plan_id)
    cambios = data.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] is not None:
        plan.nombre = cambios["nombre"].strip()
    if "cantidadMin" in cambios and cambios["cantidadMin"] is not None:
        plan.cantidad_min = cambios["cantidadMin"]
    if "cantidadMax" in cambios:  # None válido = "en adelante"
        plan.cantidad_max = cambios["cantidadMax"]
    if "precioUnitario" in cambios and cambios["precioUnitario"] is not None:
        plan.precio_unitario = cambios["precioUnitario"]
    if "activo" in cambios and cambios["activo"] is not None:
        plan.activo = cambios["activo"]
    _validar_rango(plan.cantidad_min, plan.cantidad_max)
    db.commit()
    db.refresh(plan)
    return _publico(plan)


def eliminar_plan(db: Session, plan_id) -> dict:
    plan = _obtener(db, plan_id)
    db.delete(plan)
    db.commit()
    return {"message": "Plan eliminado correctamente."}
