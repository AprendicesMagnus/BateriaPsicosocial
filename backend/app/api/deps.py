from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.core.roles import ROLES_EVALUADOR
from app.core.errors import AppError
from app.core.security import decodificar_token
from app.db.session import get_db
from app.models.organization import Organizacion
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


def get_current_user_opcional(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Devuelve el usuario si llega un token; None si la petición es anónima."""
    if credenciales is None:
        return None
    return get_current_user(request, credenciales, db)


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
    if usuario.rol.codigo != "SUPER_ADMINISTRADOR":
        raise AppError(403, "Esta acción está restringida al administrador del sistema.")
    return usuario


def require_gestor(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.rol.codigo not in {"SUPER_ADMINISTRADOR", *ROLES_EVALUADOR}:
        raise AppError(403, "Esta acción requiere permisos de administrador o evaluador SST.")
    return usuario


# --- Permisos de Reportes por rol -----------------------------------------------------------
# SUPER_ADMINISTRADOR : todas las empresas.
# EVALUADOR_SST       : su empresa ACTIVA (el Psicologo elige entre las que creó); todo el Dashboard,
#                       incluidos resultados individuales (encuestas realizadas).
# RESPONSABLE_SST     : su empresa; mismos permisos que el Psicologo dentro de ella (ROLES_EVALUADOR).
# ADMINISTRADOR       : las empresas que él creó; reportes por área y generar/descargar informes agrupados.
# JEFE                : las empresas que él creó; solo CONSULTA de reportes por área (no descarga informes).
# Los resultados individuales (encuestas realizadas) son confidenciales: solo SUPER_ADMINISTRADOR y quienes gestionan la empresa.
ROLES_POR_CREADOR = {"JEFE", "ADMINISTRADOR"}  # su alcance son las empresas que crearon
ROLES_LECTORES_REPORTES = {"SUPER_ADMINISTRADOR", "EVALUADOR_SST", "RESPONSABLE_SST", "JEFE", "ADMINISTRADOR"}
ROLES_GENERADORES_INFORMES = ROLES_LECTORES_REPORTES - {"JEFE"}


def require_lector_reportes(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Acceso de lectura a Reportes por área."""
    if usuario.rol.codigo not in ROLES_LECTORES_REPORTES:
        raise AppError(403, "Tu rol no tiene acceso a los reportes.")
    return usuario


def require_generador_informes(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Generar y descargar informes agrupados (el Jefe solo consulta)."""
    if usuario.rol.codigo not in ROLES_GENERADORES_INFORMES:
        raise AppError(403, "Tu rol solo puede consultar los reportes; no puede generar ni descargar informes.")
    return usuario


def es_administrador(usuario: Usuario) -> bool:
    return usuario.rol.codigo == "SUPER_ADMINISTRADOR"


def es_evaluador(usuario: Usuario) -> bool:
    return usuario.rol.codigo in ROLES_EVALUADOR


def asegurar_acceso_organizacion(usuario: Usuario, organizacion_id: UUID) -> None:
    if es_administrador(usuario):
        return
    if usuario.organizacion_id != organizacion_id:
        raise AppError(403, "No tiene acceso a esta organización.")


def puede_acceder_organizacion(db: Session, usuario: Usuario, organizacion_id: UUID) -> bool:
    """Super Administrador: todas. Jefe/Administrador: las que creó. Resto: la suya."""
    if es_administrador(usuario):
        return True
    if usuario.rol.codigo in ROLES_POR_CREADOR:
        return (
            db.query(Organizacion.id)
            .filter(Organizacion.id == organizacion_id, Organizacion.creada_por_id == usuario.id)
            .first()
            is not None
        )
    return usuario.organizacion_id == organizacion_id


def asegurar_acceso_organizacion_db(db: Session, usuario: Usuario, organizacion_id: UUID) -> None:
    if not puede_acceder_organizacion(db, usuario, organizacion_id):
        raise AppError(403, "No tiene acceso a esta organización.")
