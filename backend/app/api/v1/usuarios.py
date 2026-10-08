from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin, require_gestor
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import CambioPasswordPerfilRequest, EmpresaActivaRequest, CambioRolRequest, UsuarioCreate, UsuarioUpdate
from app.services import auditoria as auditoria_service
from app.services import organizaciones as organizaciones_service
from app.services import perfil as perfil_service
from app.services import usuarios as usuarios_service
from app.services.auth import usuario_publico

router = APIRouter()


# --- Perfil propio y directorio (declaradas antes de /{usuario_id}) ---------------------------


@router.patch("/me")
def editar_mi_perfil(
    request: Request,
    nombre: str | None = Form(default=None),
    apellido: str | None = Form(default=None),
    foto: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    contenido = foto.file.read(perfil_service.MAX_FOTO_BYTES + 1) if foto is not None else None
    usuario = perfil_service.editar_perfil(db, actual, nombre=nombre, apellido=apellido, foto=contenido)
    auditoria_service.registrar_auditoria(
        db, usuario=actual, accion="EDITAR_PERFIL", entidad="Usuario", entidad_id=str(actual.id), request=request
    )
    return {"usuario": usuario_publico(usuario)}


@router.post("/me/password")
def cambiar_mi_password(
    data: CambioPasswordPerfilRequest,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    usuario = perfil_service.cambiar_password(db, actual, data.passwordActual, data.passwordNueva)
    auditoria_service.registrar_auditoria(
        db, usuario=actual, accion="CAMBIAR_PASSWORD_PERFIL", entidad="Usuario", entidad_id=str(actual.id), request=request
    )
    return {"message": "Contraseña actualizada correctamente.", "usuario": usuario_publico(usuario)}


@router.post("/me/empresa-activa")
def cambiar_mi_empresa_activa(
    data: EmpresaActivaRequest,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    usuario = organizaciones_service.cambiar_empresa_activa(db, actual, data.organizacionId)
    auditoria_service.registrar_auditoria(
        db, usuario=actual, accion="CAMBIAR_EMPRESA_ACTIVA", entidad="Organizacion",
        entidad_id=str(data.organizacionId), request=request,
    )
    return {"usuario": usuario_publico(usuario)}


@router.get("/directorio")
def directorio_usuarios(
    q: str | None = Query(default=None, max_length=100),
    limite: int = Query(default=25, ge=1, le=100),
    desplazamiento: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _actual: Usuario = Depends(require_admin),
):
    """Solo Super Administrador. Devuelve nombre completo, correo y rol de cada usuario."""
    return perfil_service.listar_directorio(db, q, limite, desplazamiento)


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


@router.patch("/{usuario_id}/rol")
def cambiar_rol_usuario(
    usuario_id: UUID,
    data: CambioRolRequest,
    request: Request,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_admin),
):
    """Cambia el rol de un usuario existente.

    Solo los Administradores pueden invocar este endpoint.
    No se permite quitar el rol ADMINISTRADOR al único administrador activo del sistema.
    """
    res = usuarios_service.cambiar_rol_usuario(db, usuario_id, data.rolCodigo, actual)
    auditoria_service.registrar_auditoria(
        db,
        usuario=actual,
        accion="CAMBIAR_ROL_USUARIO",
        entidad="Usuario",
        entidad_id=str(usuario_id),
        request=request,
        detalle={"rol_anterior": res.get("rol_anterior"), "rol_nuevo": data.rolCodigo},
    )
    return res


@router.get("/{usuario_id}/compras")
def listar_compras_usuario(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    from app.services import compras as compras_service
    return compras_service.listar_compras_usuario(db, usuario_id, actual)


@router.get("/trabajadores/{organizacion_id}")
def listar_trabajadores(
    organizacion_id: UUID,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    return usuarios_service.listar_trabajadores(db, organizacion_id, actual)
