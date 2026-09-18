from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UsuarioPublico(BaseModel):
    id: UUID
    nombre: str
    apellido: str
    email: EmailStr
    rol: str
    emailVerificado: bool
    estado: str
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = None
    cargo: str | None = None

    model_config = {"from_attributes": True}


class RegistroRequest(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerificarEmailRequest(BaseModel):
    email: EmailStr
    codigo: str = Field(pattern=r"^\d{6}$", description="Código de 6 dígitos")


class ReenviarCodigoRequest(BaseModel):
    email: EmailStr
    tipo: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    codigo: str = Field(pattern=r"^\d{6}$", description="Código de 6 dígitos")


class ResetPasswordRequest(BaseModel):
    resetToken: str
    password: str


class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    rolCodigo: str
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = None
    cargo: str | None = None


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    rolCodigo: str | None = None
    estado: str | None = None
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = None
    cargo: str | None = None


class RolCreate(BaseModel):
    codigo: str = Field(min_length=3, max_length=50)
    nombre: str
    descripcion: str | None = None
    permisos: list[str] = []


class RolUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    permisos: list[str] | None = None
    activo: bool | None = None


class CambioRolRequest(BaseModel):
    rol_codigo: str = Field(min_length=2, max_length=50)


class OrganizacionCreate(BaseModel):
    nombre: str
    nit: str = Field(pattern=r"^\d{9}$", description="NIT debe contener 9 dígitos")
    sector: str | None = None
    municipio: str | None = None
    telefono: str | None = Field(default=None, pattern=r"^\d{7,10}$", description="Teléfono debe contener 7-10 dígitos")
    email: EmailStr | None = None


class OrganizacionUpdate(BaseModel):
    nombre: str | None = None
    nit: str | None = None
    sector: str | None = None
    municipio: str | None = None
    telefono: str | None = Field(default=None, pattern=r"^\d{7,10}$", description="Teléfono debe contener 7-10 dígitos")
    email: EmailStr | None = None
    activa: bool | None = None


class AreaCreate(BaseModel):
    organizacionId: UUID
    nombre: str


class AreaUpdate(BaseModel):
    nombre: str | None = None
    activa: bool | None = None


class PreguntaCreate(BaseModel):
    codigo: str
    enunciado: str
    orden: int
    inversa: bool = False
    valorMinimo: int = 1
    valorMaximo: int = 5


class DimensionCreate(BaseModel):
    codigo: str
    nombre: str
    dominio: str
    orden: int
    preguntas: list[PreguntaCreate] = []


class BaremoCreate(BaseModel):
    dimensionCodigo: str
    nivel: str
    minimo: float
    maximo: float
    orden: int


class CuestionarioCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    dimensiones: list[DimensionCreate]
    baremos: list[BaremoCreate] = []


class EvaluacionCreate(BaseModel):
    organizacionId: UUID
    nombre: str
    versionId: UUID | None = None
    trabajadoresIds: list[UUID] = []


class EvaluacionCierre(BaseModel):
    justificacion: str | None = None


class ConsentimientoRequest(BaseModel):
    aceptado: bool = True


class RespuestaRequest(BaseModel):
    preguntaId: UUID
    valor: int = Field(ge=1, le=5, description="Valor Likert entre 1 y 5")


class InformeRequest(BaseModel):
    tipo: str
    formato: str = "PDF"
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
    nit: str = Field(pattern=r"^\d{9}$", description="NIT debe contener 9 dígitos")  # solo longitud y dígitos
    nombre: str
    sector: str | None = None
    numeroTrabajadores: int | None = None
    municipio: str | None = None
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, pattern=r"^\d{7,10}$", description="Teléfono debe contener 7-10 dígitos")
    usuarioNombre: str
    usuarioApellido: str
    usuarioEmail: EmailStr
    usuarioPassword: str


class CompraCreate(BaseModel):
    cantidad: int = Field(gt=0)
    bateriaNombre: str | None = "Batería de Riesgo Psicosocial"
    organizacionId: UUID | None = None


class PagoCreate(BaseModel):
    compraId: UUID
    metodo: str
    numeroTarjeta: str | None = None
    nombreTarjeta: str | None = None
    vencimiento: str | None = None
    cvv: str | None = None
    banco: str | None = None
    monto: float | None = Field(default=None, gt=0, description="Monto del pago debe ser mayor a 0")

