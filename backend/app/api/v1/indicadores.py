from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.services import indicadores as indicadores_service

router = APIRouter()

@router.get("")
def obtener_indicadores(
    organizacion_id: UUID | None = None,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    # Si es trabajador/evaluador restringir a su organización si no especifica
    if actual.rol.codigo != "ADMINISTRADOR":
        organizacion_id = actual.organizacion_id

    return indicadores_service.obtener_resumen_indicadores(db, organizacion_id)
