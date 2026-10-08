import re
from datetime import datetime
from typing import Annotated, Literal
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


# Roles que una persona puede elegir por sí misma al registrarse.
# Nunca incluir SUPER_ADMINISTRADOR aquí.
# Nota: "EVALUADOR_SST" es el código interno de "Psicologo".
RolRegistro = Literal["JEFE", "ADMINISTRADOR", "EVALUADOR_SST"]


class RegistroRequest(BaseModel):
    nombre: NombrePersona
    apellido: NombrePersona
    email: Correo
    password: PasswordNueva
    rol: RolRegistro


class CambioPasswordPerfilRequest(BaseModel):
    passwordActual: str = Field(min_length=1, max_length=72)
    passwordNueva: PasswordNueva


class EmpresaActivaRequest(BaseModel):
    organizacionId: UUID


class LoginRequest(BaseModel):
    email: Correo
    password: str = Field(min_length=1, max_length=72)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20, description="ID token (JWT) entregado por Google Identity Services")
    # Solo es obligatorio la primera vez (cuando la cuenta aún no existe).
    rol: RolRegistro | None = None


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


# Sectores permitidos al registrar o editar una empresa desde "Crear empresa" / "Mis Empresas".
SectorEmpresa = Literal["Comercial", "Servicios", "Otros"]


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


class OrganizacionMiaUpdate(BaseModel):
    """Campos que el creador de una empresa puede editar (razón social y NIT están bloqueados)."""

    sector: SectorEmpresa | None = None
    municipio: Lugar | None = None
    email: Correo | None = None
    telefono: str | None = Field(default=None, pattern=r"^3\d{9}$", description="Celular de 10 dígitos que empieza por 3")


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
    tipoRespuesta: str = Field(default="LIKERT", max_length=20)


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
    valor: int | str = Field(description="Valor Likert entre 0 y 5 o texto")

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, v):
        if isinstance(v, int):
            # Se permite 0 porque el intralaboral usa la escala oficial 0-4 (Nunca=0 ... Siempre=4).
            # El rango exacto de cada pregunta se valida en el servicio con valor_minimo/valor_maximo.
            if v < 0 or v > 5:
                raise ValueError("El valor numérico debe estar entre 0 y 5.")
        elif isinstance(v, str):
            if not v.strip():
                raise ValueError("El valor de texto no puede estar vacío.")
        else:
            raise ValueError("Tipo de respuesta no válido.")
        return v


class FichaDatosRequest(BaseModel):
    nombreCompleto: str = Field(min_length=2, max_length=150)
    sexo: str = Field(min_length=1, max_length=20)
    anioNacimiento: str = Field(min_length=4, max_length=4)
    estadoCivil: str = Field(min_length=1, max_length=50)
    nivelEstudios: str = Field(min_length=1, max_length=80)
    ocupacion: str = Field(min_length=1, max_length=150)
    residenciaCiudad: str = Field(min_length=1, max_length=100)
    residenciaDepartamento: str = Field(min_length=1, max_length=100)
    estrato: str = Field(min_length=1, max_length=20)
    tipoVivienda: str = Field(min_length=1, max_length=50)
    personasACargo: str | int = Field(default="0")
    trabajoCiudad: str = Field(min_length=1, max_length=100)
    trabajoDepartamento: str = Field(min_length=1, max_length=100)
    antiguedadEmpresaMenosUnAnio: bool = False
    antiguedadEmpresa: str = Field(default="")
    nombreCargo: str = Field(min_length=1, max_length=150)
    tipoCargo: str = Field(min_length=1, max_length=150)
    antiguedadCargoMenosUnAnio: bool = False
    antiguedadCargo: str = Field(default="")
    areaODepartamento: str = Field(min_length=1, max_length=150)
    tipoContrato: str = Field(min_length=1, max_length=80)
    horasDiarias: str | int = Field(default="8")
    tipoSalario: str = Field(min_length=1, max_length=100)


class InstrumentoOut(BaseModel):
    instrumentoId: UUID
    versionId: UUID
    codigo: str
    nombre: str
    orden: int
    obligatorio: bool
    estado: str


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
    sector: SectorEmpresa | None = None
    numeroTrabajadores: int | None = Field(default=None, ge=1, le=1000000)
    municipio: Lugar | None = None
    email: Correo | None = None
    # Celular de contacto de la empresa: 10 dígitos y empieza por 3 (formato Colombia).
    telefono: str | None = Field(default=None, pattern=r"^3\d{9}$", description="Celular de 10 dígitos que empieza por 3")
    # Datos del usuario responsable. Son obligatorios salvo cuando quien crea la empresa es un
    # Psicologo (él mismo es el responsable); la regla se valida en el servicio.
    usuarioNombre: NombrePersona | None = None
    usuarioApellido: NombrePersona | None = None
    usuarioEmail: Correo | None = None
    usuarioPassword: PasswordNueva | None = None


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


class FinalizarCuestionarioRequest(BaseModel):
    """Cuerpo OPCIONAL de POST /evaluaciones/{evaluacion_id}/finalizar-cuestionario.

    Ejemplo: {"filtros": {"CLIENTES": false, "JEFE": true}}
    Cada clave es una pregunta filtro (atiende clientes, es jefe...) y su valor es la
    respuesta (True = Sí, False = No). El id de la evaluación ya viaja en la URL.
    """

    filtros: dict[str, bool] = Field(default_factory=dict)