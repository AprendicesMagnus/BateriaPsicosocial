import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, AliasChoices, BaseModel, BeforeValidator, EmailStr, Field, field_validator

LETRAS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
PATRON_NOMBRE_PERSONA = rf"^[{LETRAS}]+( [{LETRAS}]+)*$"
PATRON_LUGAR = rf"^[{LETRAS}][{LETRAS} .-]*$"
PATRON_TEXTO_LIBRE = rf"^[{LETRAS}0-9][{LETRAS}0-9 .,&'()/-]*$"


def normalizar_espacios(valor):
    if isinstance(valor, str):
        return " ".join(valor.split())
    return valor


def exigir_dos_letras(valor: str) -> str:
    if len(re.findall(rf"[{LETRAS}]", valor)) < 2:
        raise ValueError("Debe contener al menos dos letras.")
    return valor


def limitar_password_a_72_bytes(valor: str) -> str:
    if len(valor.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes.")
    return valor


def exigir_complejidad_password(valor: str) -> str:
    if not (re.search(r"[a-z]", valor) and re.search(r"[A-Z]", valor) and re.search(r"\d", valor)):
        raise ValueError("La contraseña debe incluir mayúsculas, minúsculas y números.")
    return valor


Correo = Annotated[EmailStr, Field(max_length=180)]

NombrePersona = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(min_length=2, max_length=100, pattern=PATRON_NOMBRE_PERSONA),
]
RazonSocial = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(min_length=2, max_length=180, pattern=PATRON_TEXTO_LIBRE),
    AfterValidator(exigir_dos_letras),
]
Lugar = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(min_length=2, max_length=80, pattern=PATRON_LUGAR),
]
Cargo = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(min_length=2, max_length=100, pattern=PATRON_TEXTO_LIBRE),
    AfterValidator(exigir_dos_letras),
]
PasswordNueva = Annotated[
    str,
    Field(min_length=8, max_length=72),
    AfterValidator(limitar_password_a_72_bytes),
    AfterValidator(exigir_complejidad_password),
]


class UsuarioPublico(BaseModel):
    id: UUID
    nombre: NombrePersona
    apellido: NombrePersona
    email: Correo
    rol: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    emailVerificado: bool
    estado: str = Field(min_length=2, max_length=20, pattern=r"^[A-Z0-9_]+$")
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = Field(default=None, pattern=r"^\d{5,15}$")
    cargo: Cargo | None = None

    model_config = {"from_attributes": True}


class RegistroRequest(BaseModel):
    nombre: NombrePersona
    apellido: NombrePersona
    email: Correo
    password: PasswordNueva


class LoginRequest(BaseModel):
    email: Correo
    password: str = Field(min_length=1, max_length=72)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20, description="ID token (JWT) entregado por Google Identity Services")


class VerificarEmailRequest(BaseModel):
    email: Correo
    codigo: str = Field(pattern=r"^\d{6}$", description="Código de 6 dígitos")


class ReenviarCodigoRequest(BaseModel):
    email: Correo
    tipo: str = Field(pattern=r"^(VERIFICACION_EMAIL|RESET_PASSWORD)$")


class ForgotPasswordRequest(BaseModel):
    email: Correo


class VerifyResetCodeRequest(BaseModel):
    email: Correo
    codigo: str = Field(pattern=r"^\d{6}$", description="Código de 6 dígitos")


class ResetPasswordRequest(BaseModel):
    resetToken: str = Field(min_length=20, max_length=1024)
    password: PasswordNueva


class UsuarioCreate(BaseModel):
    nombre: NombrePersona
    apellido: NombrePersona
    email: Correo
    password: PasswordNueva
    rolCodigo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = Field(default=None, pattern=r"^\d{5,15}$")
    cargo: Cargo | None = None


class UsuarioUpdate(BaseModel):
    nombre: NombrePersona | None = None
    apellido: NombrePersona | None = None
    rolCodigo: str | None = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    estado: str | None = Field(default=None, min_length=2, max_length=20, pattern=r"^[A-Z0-9_]+$")
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = Field(default=None, pattern=r"^\d{5,15}$")
    cargo: Cargo | None = None


class RolCreate(BaseModel):
    codigo: str = Field(min_length=3, max_length=50, pattern=r"^[A-Z0-9_]+$")
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    permisos: list[Annotated[str, Field(min_length=3, max_length=80, pattern=r"^[A-Z0-9_]+$")]] = []


class RolUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    permisos: list[Annotated[str, Field(min_length=3, max_length=80, pattern=r"^[A-Z0-9_]+$")]] | None = None
    activo: bool | None = None


class CambioRolRequest(BaseModel):
    rolCodigo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$", validation_alias=AliasChoices("rolCodigo", "rol_codigo"))


class OrganizacionCreate(BaseModel):
    nombre: RazonSocial
    nit: str = Field(pattern=r"^\d{9}(-\d)?$", description="NIT en formato 9 dígitos base o NNNNNNNNN-D")
    sector: str | None = Field(default=None, min_length=2, max_length=80)
    municipio: Lugar | None = None
    telefono: str | None = Field(default=None, pattern=r"^\d{7,10}$", description="Teléfono debe contener 7-10 dígitos")
    email: Correo | None = None
    numeroTrabajadores: int | None = Field(default=None, ge=1, le=1000000, description="Número de trabajadores entre 1 y 1.000.000")


class OrganizacionUpdate(BaseModel):
    nombre: RazonSocial | None = None
    nit: str | None = Field(default=None, pattern=r"^\d{9}(-\d)?$")
    sector: str | None = Field(default=None, min_length=2, max_length=80)
    municipio: Lugar | None = None
    telefono: str | None = Field(default=None, pattern=r"^\d{7,10}$", description="Teléfono debe contener 7-10 dígitos")
    email: Correo | None = None
    numeroTrabajadores: int | None = Field(default=None, ge=1, le=1000000)
    activa: bool | None = None


class AreaCreate(BaseModel):
    organizacionId: UUID
    nombre: str = Field(min_length=2, max_length=120)


class AreaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    activa: bool | None = None


class PreguntaCreate(BaseModel):
    codigo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    enunciado: str = Field(min_length=5, max_length=2000)
    orden: int = Field(gt=0)
    inversa: bool = False
    valorMinimo: int = Field(default=1, ge=1, le=5)
    valorMaximo: int = Field(default=5, ge=1, le=5)


class DimensionCreate(BaseModel):
    codigo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    nombre: str = Field(min_length=2, max_length=150)
    dominio: str = Field(min_length=2, max_length=150)
    orden: int = Field(gt=0)
    preguntas: list[PreguntaCreate] = []


class BaremoCreate(BaseModel):
    dimensionCodigo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    nivel: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    minimo: float
    maximo: float
    orden: int = Field(gt=0)


class CuestionarioCreate(BaseModel):
    codigo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)
    dimensiones: list[DimensionCreate]
    baremos: list[BaremoCreate] = []


class EvaluacionCreate(BaseModel):
    organizacionId: UUID
    nombre: str = Field(min_length=2, max_length=150)
    versionId: UUID | None = None
    trabajadoresIds: list[UUID] = []


class EvaluacionCierre(BaseModel):
    justificacion: str | None = Field(default=None, max_length=1000)


class ConsentimientoRequest(BaseModel):
    aceptado: bool = True


class RespuestaRequest(BaseModel):
    preguntaId: UUID
    valor: int = Field(ge=1, le=5, description="Valor Likert entre 1 y 5")


class InformeRequest(BaseModel):
    tipo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    formato: str = Field(default="PDF", pattern=r"^(PDF|EXCEL|CSV)$")
    trabajadorId: UUID | None = None
    areaId: UUID | None = None


class AuditoriaOut(BaseModel):
    id: UUID
    usuarioId: UUID | None
    accion: str
    entidad: str | None
    entidadId: str | None
    ipOrigen: str | None
    detalle: dict | None
    registradoEn: datetime


class OrganizacionAutorregistroCreate(BaseModel):
    nit: str = Field(pattern=r"^\d{9}-\d$", description="NIT en formato NNNNNNNNN-D (9 dígitos base, guion, dígito verificador)")
    nombre: RazonSocial
    sector: str | None = Field(default=None, min_length=2, max_length=80)
    numeroTrabajadores: int | None = Field(default=None, ge=1, le=1000000)
    municipio: Lugar | None = None
    email: Correo | None = None
    telefono: str | None = Field(default=None, pattern=r"^\d{7,10}$", description="Teléfono debe contener 7-10 dígitos")
    usuarioNombre: NombrePersona
    usuarioApellido: NombrePersona
    usuarioEmail: Correo
    usuarioPassword: PasswordNueva


class CompraCreate(BaseModel):
    cantidad: int = Field(gt=0, le=100000)
    bateriaNombre: str | None = Field(default="Batería de Riesgo Psicosocial", max_length=150)
    organizacionId: UUID | None = None


class PagoCreate(BaseModel):
    compraId: UUID
    metodo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    numeroTarjeta: str | None = Field(default=None, pattern=r"^\d{13,19}$")
    nombreTarjeta: NombrePersona | None = None
    vencimiento: str | None = Field(default=None, pattern=r"^(0[1-9]|1[0-2])\/\d{2}$")
    cvv: str | None = Field(default=None, pattern=r"^\d{3,4}$")
    banco: str | None = Field(default=None, min_length=2, max_length=100)
    monto: float | None = Field(default=None, gt=0, description="Monto del pago debe ser mayor a 0")

    @field_validator("numeroTarjeta", mode="before")
    @classmethod
    def normalizar_numero_tarjeta(cls, valor):
        return valor.replace(" ", "") if isinstance(valor, str) else valor