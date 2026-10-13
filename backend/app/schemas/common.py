import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    AliasChoices,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    field_validator,
)

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
    if not (
        re.search(r"[a-z]", valor)
        and re.search(r"[A-Z]", valor)
        and re.search(r"\d", valor)
    ):
        raise ValueError(
            "La contraseña debe incluir mayúsculas, minúsculas y números."
        )
    return valor


Correo = Annotated[EmailStr, Field(max_length=180)]

NombrePersona = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(
        min_length=2,
        max_length=100,
        pattern=PATRON_NOMBRE_PERSONA,
    ),
]

RazonSocial = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(
        min_length=2,
        max_length=180,
        pattern=PATRON_TEXTO_LIBRE,
    ),
    AfterValidator(exigir_dos_letras),
]

Lugar = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(
        min_length=2,
        max_length=80,
        pattern=PATRON_LUGAR,
    ),
]

Cargo = Annotated[
    str,
    BeforeValidator(normalizar_espacios),
    Field(
        min_length=2,
        max_length=100,
        pattern=PATRON_TEXTO_LIBRE,
    ),
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
    rol: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    emailVerificado: bool
    estado: str = Field(
        min_length=2,
        max_length=20,
        pattern=r"^[A-Z0-9_]+$",
    )
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = Field(
        default=None,
        pattern=r"^\d{5,15}$",
    )
    cargo: Cargo | None = None

    model_config = {"from_attributes": True}


# Roles que una persona puede elegir por sí misma al registrarse.
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
    credential: str = Field(
        min_length=20,
        description="ID token (JWT) entregado por Google Identity Services",
    )
    rol: RolRegistro | None = None


class VerificarEmailRequest(BaseModel):
    email: Correo
    codigo: str = Field(
        pattern=r"^\d{6}$",
        description="Código de 6 dígitos",
    )


class ReenviarCodigoRequest(BaseModel):
    email: Correo
    tipo: str = Field(pattern=r"^(VERIFICACION_EMAIL|RESET_PASSWORD)$")


class ForgotPasswordRequest(BaseModel):
    email: Correo


class VerifyResetCodeRequest(BaseModel):
    email: Correo
    codigo: str = Field(
        pattern=r"^\d{6}$",
        description="Código de 6 dígitos",
    )


class ResetPasswordRequest(BaseModel):
    resetToken: str = Field(min_length=20, max_length=1024)
    password: PasswordNueva


class UsuarioCreate(BaseModel):
    nombre: NombrePersona
    apellido: NombrePersona
    email: Correo
    password: PasswordNueva
    rolCodigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = Field(
        default=None,
        pattern=r"^\d{5,15}$",
    )
    cargo: Cargo | None = None


class UsuarioUpdate(BaseModel):
    nombre: NombrePersona | None = None
    apellido: NombrePersona | None = None
    rolCodigo: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    estado: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
        pattern=r"^[A-Z0-9_]+$",
    )
    organizacionId: UUID | None = None
    areaId: UUID | None = None
    numeroIdentificacion: str | None = Field(
        default=None,
        pattern=r"^\d{5,15}$",
    )
    cargo: Cargo | None = None


class RolCreate(BaseModel):
    codigo: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    permisos: list[
        Annotated[
            str,
            Field(
                min_length=3,
                max_length=80,
                pattern=r"^[A-Z0-9_]+$",
            ),
        ]
    ] = []


class RolUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    permisos: list[
        Annotated[
            str,
            Field(
                min_length=3,
                max_length=80,
                pattern=r"^[A-Z0-9_]+$",
            ),
        ]
    ] | None = None
    activo: bool | None = None


class CambioRolRequest(BaseModel):
    rolCodigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
        validation_alias=AliasChoices("rolCodigo", "rol_codigo"),
    )


# Sectores permitidos al registrar o editar una empresa desde "Crear empresa" / "Mis Empresas".
SectorEmpresa = Literal["Comercial", "Servicios", "Otros"]


class OrganizacionCreate(BaseModel):
    nombre: RazonSocial
    nit: str = Field(
        pattern=r"^\d{9}(-\d)?$",
        description="NIT de 9 dígitos, opcionalmente seguido de guion y dígito",
    )
    sector: str | None = Field(default=None, min_length=2, max_length=80)
    municipio: Lugar | None = None
    telefono: str | None = Field(
        default=None,
        pattern=r"^\d{7,10}$",
        description="Teléfono de 7 a 10 dígitos",
    )
    email: Correo | None = None
    numeroTrabajadores: int | None = Field(
        default=None,
        ge=1,
        le=1000000,
    )


class OrganizacionUpdate(BaseModel):
    nombre: RazonSocial | None = None
    nit: str | None = Field(default=None, pattern=r"^\d{9}(-\d)?$")
    sector: str | None = Field(default=None, min_length=2, max_length=80)
    municipio: Lugar | None = None
    telefono: str | None = Field(default=None, pattern=r"^\d{7,10}$")
    email: Correo | None = None
    numeroTrabajadores: int | None = Field(
        default=None,
        ge=1,
        le=1000000,
    )
    activa: bool | None = None


class OrganizacionMiaUpdate(BaseModel):
    """Campos que el creador de una empresa puede editar (razón social y NIT están bloqueados)."""

    sector: SectorEmpresa | None = None
    municipio: Lugar | None = None
    email: Correo | None = None
    telefono: str | None = Field(default=None, pattern=r"^3\d{9}$", description="Celular de 10 dígitos que empieza por 3")


class ResponsableEmpresaUpdate(BaseModel):
    """Datos que se pueden editar del usuario responsable de una empresa (correo y contraseña no)."""

    nombre: NombrePersona | None = None
    apellido: NombrePersona | None = None
    numeroResolucion: str | None = Field(default=None, pattern=r"^\d{6}$", description="6 dígitos numéricos")


class AreaCreate(BaseModel):
    organizacionId: UUID
    nombre: str = Field(min_length=2, max_length=120)


class AreaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    activa: bool | None = None


class PreguntaCreate(BaseModel):
    codigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    enunciado: str = Field(min_length=5, max_length=2000)
    orden: int = Field(gt=0)
    inversa: bool = False
    valorMinimo: int = Field(default=1, ge=1, le=5)
    valorMaximo: int = Field(default=5, ge=1, le=5)
    tipoRespuesta: str = Field(default="LIKERT", max_length=20)


class DimensionCreate(BaseModel):
    codigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    nombre: str = Field(min_length=2, max_length=150)
    dominio: str = Field(min_length=2, max_length=150)
    orden: int = Field(gt=0)
    preguntas: list[PreguntaCreate] = []


class BaremoCreate(BaseModel):
    dimensionCodigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    nivel: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    minimo: float
    maximo: float
    orden: int = Field(gt=0)


class CuestionarioCreate(BaseModel):
    codigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = Field(default=None, max_length=1000)
    dimensiones: list[DimensionCreate] = []


class CompraCreate(BaseModel):
    cantidad: int = Field(gt=0)
    organizacionId: UUID | None = None
    bateriaNombre: str | None = None


class RespuestaEnvio(BaseModel):
    preguntaCodigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
    )
    valor: int = Field(ge=1, le=5)


class EvaluacionEnviarRespuestas(BaseModel):
    respuestas: list[RespuestaEnvio]


class EvaluacionCierre(BaseModel):
    notas: str | None = Field(default=None, max_length=2000)


class EvaluacionPublica(BaseModel):
    id: UUID
    usuarioId: UUID
    cuestionarioCodigo: str
    estado: str
    creadoEn: datetime
    finalizadoEn: datetime | None = None
    puntuaciones: dict | None = None

    model_config = {"from_attributes": True}


class EvaluacionCreate(BaseModel):
    organizacionId: UUID
    nombre: str = Field(min_length=2, max_length=200)
    versionId: UUID | None = None
    trabajadoresIds: list[UUID] = Field(default_factory=list)


class PagoPublico(BaseModel):
    id: UUID
    compraId: UUID
    metodo: str
    referencia: str
    monto: float
    estado: str
    banco: str | None = None
    ultimosDigitos: str | None = None
    titular: str | None = None
    mensajeRespuesta: str | None = None
    procesadoEn: datetime

    model_config = {"from_attributes": True}


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
    # Acepta tanto las claves snake_case del backend como las camelCase
    # del formulario web.
    nombre_completo: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
        validation_alias=AliasChoices(
            "nombre_completo",
            "nombreCompleto",
        ),
    )

    sexo: Literal["MASCULINO", "FEMENINO"] = Field(
        validation_alias=AliasChoices("sexo"),
    )

    ano_nacimiento: int = Field(
        ge=1930,
        le=2020,
        validation_alias=AliasChoices(
            "ano_nacimiento",
            "anioNacimiento",
            "anoNacimiento",
        ),
    )

    estado_civil: str = Field(
        min_length=2,
        max_length=40,
        validation_alias=AliasChoices("estado_civil", "estadoCivil"),
    )

    nivel_estudios: str = Field(
        min_length=2,
        max_length=80,
        validation_alias=AliasChoices("nivel_estudios", "nivelEstudios"),
    )

    ocupacion: str = Field(min_length=2, max_length=120)

    ciudad_residencia: Lugar = Field(
        validation_alias=AliasChoices(
            "ciudad_residencia",
            "residenciaCiudad",
        ),
    )

    departamento_residencia: Lugar = Field(
        validation_alias=AliasChoices(
            "departamento_residencia",
            "residenciaDepartamento",
        ),
    )

    estrato: int = Field(ge=1, le=6)

    tipo_vivienda: str = Field(
        min_length=2,
        max_length=40,
        validation_alias=AliasChoices("tipo_vivienda", "tipoVivienda"),
    )

    personas_a_cargo: int = Field(
        ge=0,
        le=20,
        validation_alias=AliasChoices(
            "personas_a_cargo",
            "personasACargo",
        ),
    )

    antiguedad_empresa: str = Field(
        min_length=1,
        max_length=40,
        validation_alias=AliasChoices(
            "antiguedad_empresa",
            "antiguedadEmpresa",
        ),
    )

    cargo_tipo: str = Field(
        min_length=2,
        max_length=100,
        validation_alias=AliasChoices(
            "cargo_tipo",
            "tipoCargo",
            "nombreCargo",
        ),
    )

    tipo_contrato: str = Field(
        min_length=2,
        max_length=60,
        validation_alias=AliasChoices("tipo_contrato", "tipoContrato"),
    )

    horas_diarias: int = Field(
        ge=1,
        le=24,
        validation_alias=AliasChoices("horas_diarias", "horasDiarias"),
    )

    salario_rango: str | None = Field(
        default=None,
        min_length=1,
        max_length=60,
        validation_alias=AliasChoices(
            "salario_rango",
            "salarioRango",
            "tipoSalario",
        ),
    )

    # Campos adicionales que envía el formulario actual.
    trabajo_ciudad: str | None = Field(
        default=None,
        validation_alias=AliasChoices("trabajo_ciudad", "trabajoCiudad"),
    )
    trabajo_departamento: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "trabajo_departamento",
            "trabajoDepartamento",
        ),
    )
    antiguedad_empresa_menos_un_anio: bool | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "antiguedad_empresa_menos_un_anio",
            "antiguedadEmpresaMenosUnAnio",
        ),
    )
    antiguedad_cargo_menos_un_anio: bool | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "antiguedad_cargo_menos_un_anio",
            "antiguedadCargoMenosUnAnio",
        ),
    )
    antiguedad_cargo: str | None = Field(
        default=None,
        validation_alias=AliasChoices("antiguedad_cargo", "antiguedadCargo"),
    )
    area_departamento: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "area_departamento",
            "areaODepartamento",
        ),
    )

    @field_validator("sexo", mode="before")
    @classmethod
    def normalizar_sexo(cls, valor):
        if isinstance(valor, str):
            normalizado = valor.strip().upper()
            equivalencias = {
                "MASCULINO": "MASCULINO",
                "FEMENINO": "FEMENINO",
            }
            return equivalencias.get(normalizado, valor)
        return valor

    @field_validator("ano_nacimiento", "estrato", "personas_a_cargo",
                     "horas_diarias", mode="before")
    @classmethod
    def convertir_enteros_desde_formulario(cls, valor):
        if isinstance(valor, str):
            valor = valor.strip()
            if valor.isdigit():
                return int(valor)
        return valor

    model_config = {"populate_by_name": True}


class FinalizarCuestionarioRequest(BaseModel):
    finalizado: bool = Field(default=True)
    filtros: dict[str, bool] = Field(default_factory=dict)


class RespuestaRequest(BaseModel):
    pregunta_codigo: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Z0-9_$]+$",
    )
    valor: int = Field(ge=0, le=5)


class OrganizacionAutorregistroCreate(BaseModel):
    nombre: RazonSocial
    nit: str = Field(
        min_length=11,
        max_length=11,
        pattern=r"^\d{9}-\d$",
        description="NIT con dígito de verificación, formato NNNNNNNNN-D",
    )
    sector: SectorEmpresa | None = None
    numeroTrabajadores: int | None = Field(default=None, ge=1, le=1000000)

    municipio: Lugar | None = None
    telefono: str | None = Field(
        default=None,
        pattern=r"^\d{7,10}$",
        description="Teléfono de 7 a 10 dígitos",
    )
    email: Correo | None = None
    numeroTrabajadores: int | None = Field(default=None, ge=1, le=1000000)

    # Celular de contacto de la empresa: 10 dígitos y empieza por 3 (formato Colombia).
    telefono: str | None = Field(
        default=None, 
        pattern=r"^3\d{9}$", 
        description="Celular de 10 dígitos que empieza por 3"
    )

    # Datos del usuario responsable. Son opcionales porque un psicólogo
    # (EVALUADOR_SST) que registra una empresa no necesita crear otro usuario;
    # el servicio responde 400 si faltan en los casos que sí los requieren.
    # Los nombres de atributo son los que usan el servicio y el frontend
    # (usuarioEmail, ...); también se aceptan los nombres *_administrador.
    usuarioEmail: Correo | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "usuarioEmail",
            "email_administrador",
            "emailAdministrador",
        ),
    )
    usuarioNombre: NombrePersona | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "usuarioNombre",
            "nombre_administrador",
            "nombreAdministrador",
        ),
    )
    usuarioApellido: NombrePersona | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "usuarioApellido",
            "apellido_administrador",
            "apellidoAdministrador",
        ),
    )
    usuarioPassword: PasswordNueva | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "usuarioPassword",
            "password_administrador",
            "passwordAdministrador",
        ),
    )
    
    # Número de resolución del responsable: exactamente 6 dígitos numéricos.
    usuarioNumeroResolucion: str | None = Field(
        default=None, 
        pattern=r"^\d{6}$", 
        description="6 dígitos numéricos"
    )

    model_config = {"populate_by_name": True}


class OrganizacionPublica(BaseModel):
    id: UUID
    nombre: str
    nit: str
    sector: str | None = None
    municipio: str | None = None
    telefono: str | None = None
    email: str | None = None
    numeroTrabajadores: int | None = Field(
        default=None,
        alias="numero_trabajadores",
    )
    activa: bool

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PagoCreate(BaseModel):
    compraId: UUID
    wompiTransactionId: str = Field(min_length=1, max_length=100)
    wompiPaymentMethod: str | None = None
    banco: str | None = None


class PagoUpdate(BaseModel):
    estado: str
    mensajeRespuesta: str | None = None
