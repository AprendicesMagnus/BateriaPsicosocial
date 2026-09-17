from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_gestor
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import UsuarioCreate, UsuarioUpdate
from app.services import auditoria as auditoria_service
from app.services import usuarios as usuarios_service

router = APIRouter()


@router.get("")
def listar_usuarios(
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return usuarios_service.listar_usuarios(db, actual)


@router.post("")
def crear_usuario(
    data: UsuarioCreate,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    res = usuarios_service.crear_usuario(db, data, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="CREAR_USUARIO",
        entidad="Usuario",
        entidad_id=res["id"],
        request=request,
    )
    return res


@router.patch("/{usuario_id}")
def actualizar_usuario(
    usuario_id: UUID,
    data: UsuarioUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    res = usuarios_service.actualizar_usuario(db, usuario_id, data, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="ACTUALIZAR_USUARIO",
        entidad="Usuario",
        entidad_id=str(usuario_id),
        request=request,
    )
    return res


@router.delete("/{usuario_id}")
def desactivar_usuario(
    usuario_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_gestor),
):
    res = usuarios_service.desactivar_usuario(db, usuario_id, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="DESACTIVAR_USUARIO",
        entidad="Usuario",
        entidad_id=str(usuario_id),
        request=request,
    )
    return res


@router.get("/trabajadores/{organizacion_id}")
def listar_trabajadores(
    organizacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return usuarios_service.listar_trabajadores(db, organizacion_id, actual)
