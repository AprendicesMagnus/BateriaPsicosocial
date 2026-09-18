from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin, require_gestor
from app.db.session import get_db
from app.models.organization import Area, Organizacion
from app.models.user import Usuario
from app.schemas.common import (
    AreaCreate,
    AreaUpdate,
    OrganizacionAutorregistroCreate,
    OrganizacionCreate,
    OrganizacionUpdate,
)
from app.services import organizaciones as organizaciones_service

router = APIRouter()


def _organizacion_publica(org: Organizacion) -> dict:
    return {
        "id": str(org.id),
        "nombre": org.nombre,
        "nit": org.nit,
        "sector": org.sector,
        "municipio": org.municipio,
        "telefono": org.telefono,
        "email": org.email,
        "activa": org.activa,
        "creadoEn": org.creado_en.isoformat(),
    }


def _area_publica(area: Area) -> dict:
    return {
        "id": str(area.id),
        "organizacionId": str(area.organizacion_id),
        "nombre": area.nombre,
        "activa": area.activa,
        "creadoEn": area.creado_en.isoformat(),
    }


@router.get("/existe")
def verificar_existe_nit(nit: str, db: Session = Depends(get_db)):
    return organizaciones_service.existe_organizacion_nit(db, nit)


@router.post("/autorregistro")
def autorregistrar_organizacion(
    data: OrganizacionAutorregistroCreate,
    db: Session = Depends(get_db),
):
    return organizaciones_service.autorregistrar_organizacion(db, data)


@router.get("")
def listar_organizaciones(
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return [_organizacion_publica(o) for o in organizaciones_service.listar_organizaciones(db, actual)]


@router.post("")
def crear_organizacion(
    data: OrganizacionCreate,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return _organizacion_publica(organizaciones_service.crear_organizacion(db, data))


@router.patch("/{organizacion_id}")
def actualizar_organizacion(
    organizacion_id: UUID,
    data: OrganizacionUpdate,
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    return _organizacion_publica(organizaciones_service.actualizar_organizacion(db, organizacion_id, data))


@router.get("/{organizacion_id}/areas")
def listar_areas(
    organizacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return [_area_publica(a) for a in organizaciones_service.listar_areas(db, organizacion_id, actual)]


@router.post("/areas")
def crear_area(
    data: AreaCreate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return _area_publica(organizaciones_service.crear_area(db, data, actual))


@router.patch("/areas/{area_id}")
def actualizar_area(
    area_id: UUID,
    data: AreaUpdate,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return _area_publica(organizaciones_service.actualizar_area(db, area_id, data, actual))


@router.delete("/areas/{area_id}")
def eliminar_area(
    area_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    return organizaciones_service.eliminar_area(db, area_id, actual)
