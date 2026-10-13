import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, false
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import utcnow
from app.db.base import Base


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    es_sistema: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    permisos: Mapped[list["RolPermiso"]] = relationship(back_populates="rol", cascade="all, delete-orphan")
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    modulo: Mapped[str] = mapped_column(String(80), nullable=False)

    roles: Mapped[list["RolPermiso"]] = relationship(back_populates="permiso", cascade="all, delete-orphan")


class RolPermiso(Base):
    __tablename__ = "roles_permisos"
    __table_args__ = (UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permiso"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rol_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permiso_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permisos.id"), nullable=False)

    rol: Mapped[Rol] = relationship(back_populates="permisos")
    permiso: Mapped[Permiso] = relationship(back_populates="roles")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("organizacion_id", "numero_identificacion", name="uq_trabajador_identificacion_org"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO", nullable=False)
    email_verificado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizaciones.id"))
    area_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.id"))
    numero_identificacion: Mapped[str | None] = mapped_column(String(30))
    cargo: Mapped[str | None] = mapped_column(String(120))
    # Número de resolución (6 dígitos) del usuario Responsable SST que se registra con la empresa.
    numero_resolucion: Mapped[str | None] = mapped_column(String(6))
    # Ruta pública de la foto de perfil (p. ej. /api/uploads/avatars/xxx.jpg).
    foto_url: Mapped[str | None] = mapped_column(String(255))
    # Fecha de la última edición de perfil (base de la regla de 1 edición cada 15 días).
    perfil_actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Paciente que responde por un enlace público: no tiene contraseña conocida ni puede iniciar sesión
    es_invitado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)

    rol: Mapped[Rol] = relationship(back_populates="usuarios")
    organizacion: Mapped["Organizacion | None"] = relationship(
        back_populates="usuarios", foreign_keys=[organizacion_id]
    )
    area: Mapped["Area | None"] = relationship(back_populates="trabajadores")
    codigos: Mapped[list["CodigoVerificacion"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    compras: Mapped[list["Compra"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class CodigoVerificacion(Base):
    __tablename__ = "codigos_verificacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    usuario: Mapped[Usuario] = relationship(back_populates="codigos")
