from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.core.security import decodificar_token
from app.db.session import get_db
from app.models.user import Permiso, Rol, RolPermiso, Usuario

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credenciales is None:
        raise AppError(401, "No autenticado.")
    payload = decodificar_token(credenciales.credentials)
    if payload.get("purpose") == "reset_password":
        raise AppError(401, "Sesión inválida o expirada.")
    usuario_id = payload.get("sub")
    usuario = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.rol)
            .joinedload(Rol.permisos)
            .joinedload(RolPermiso.permiso)
        )
        .filter(Usuario.id == usuario_id)
        .first()
    )
    if usuario is None:
        raise AppError(401, "Sesión inválida o expirada.")
    if usuario.estado != "ACTIVO":
        raise AppError(403, "Esta cuenta se encuentra inactiva.")
    request.state.usuario = usuario
    return usuario


def require_permisos(*codigos: str) -> Callable:
    def dependencia(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if not tiene_permisos(usuario, set(codigos)):
            raise AppError(403, "No tiene permisos para realizar esta acción.")
        return usuario

    return dependencia


def tiene_permisos(usuario: Usuario, codigos: set[str]) -> bool:
    actuales = {rp.permiso.codigo for rp in usuario.rol.permisos}
    return codigos.issubset(actuales)


def require_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.rol.codigo != "ADMINISTRADOR":
        raise AppError(403, "Esta acción está restringida al administrador del sistema.")
    return usuario


def require_gestor(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.rol.codigo not in {"ADMINISTRADOR", "EVALUADOR_SST"}:
        raise AppError(403, "Esta acción requiere permisos de administrador o evaluador SST.")
    return usuario


def es_administrador(usuario: Usuario) -> bool:
    return usuario.rol.codigo == "ADMINISTRADOR"


def es_evaluador(usuario: Usuario) -> bool:
    return usuario.rol.codigo == "EVALUADOR_SST"


def asegurar_acceso_organizacion(usuario: Usuario, organizacion_id: UUID) -> None:
    if es_administrador(usuario):
        return
    if usuario.organizacion_id != organizacion_id:
        raise AppError(403, "No tiene acceso a esta organización.")
