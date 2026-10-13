from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import (
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    ReenviarCodigoRequest,
    RegistroRequest,
    ResetPasswordRequest,
    VerificarEmailRequest,
    VerifyResetCodeRequest,
)
from app.services import auditoria as auditoria_service
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register")
def registrar(data: RegistroRequest, db: Session = Depends(get_db)):
    return auth_service.registrar(db, data)


@router.post("/verify-email")
def verificar_email(data: VerificarEmailRequest, db: Session = Depends(get_db)):
    return auth_service.verificar_email(db, data.email, data.codigo)


@router.post("/resend-code")
def reenviar_codigo(data: ReenviarCodigoRequest, db: Session = Depends(get_db)):
    return auth_service.reenviar_codigo(db, data.email, data.tipo)


@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    resultado = auth_service.login(db, data.email, data.password)
    auditoria_service.registrar_auditoria(
        db,
        usuario=db.get(Usuario, UUID(resultado["usuario"]["id"])),  # quién inició sesión
        accion="LOGIN",
        entidad="Usuario",
        entidad_id=resultado["usuario"]["id"],
        request=request,
    )
    return resultado


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.forgot_password(db, data.email)


@router.post("/verify-reset-code")
def verify_reset_code(data: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    return auth_service.verify_reset_code(db, data.email, data.codigo)


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.reset_password(db, data.resetToken, data.password)


@router.get("/me")
def me(usuario: Usuario = Depends(get_current_user)):
    return auth_service.me(usuario)


@router.post("/google")
def login_google(data: GoogleLoginRequest, request: Request, db: Session = Depends(get_db)):
    # Si la cuenta no existe y no llegó el rol, el servicio responde requiereRol=True
    # (no crea nada). El frontend muestra la pantalla de selección de rol y vuelve a
    # llamar a este mismo endpoint con {credential, rol}.
    resultado = auth_service.login_con_google(db, data.credential, data.rol)
    if resultado.get("requiereRol"):
        return resultado

    auditoria_service.registrar_auditoria(
        db,
        usuario=db.get(Usuario, UUID(resultado["usuario"]["id"])),  # quién inició sesión
        accion="LOGIN_GOOGLE",
        entidad="Usuario",
        entidad_id=resultado["usuario"]["id"],
        request=request,
    )
    return resultado
