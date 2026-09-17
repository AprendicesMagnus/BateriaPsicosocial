import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import utcnow
from app.db.base import Base


class CuestionarioVersion(Base):
    __tablename__ = "cuestionario_versiones"
    __table_args__ = (UniqueConstraint("codigo", "numero_version", name="uq_cuestionario_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(180), nullable=False)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    vigente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    dimensiones: Mapped[list["Dimension"]] = relationship(back_populates="version", cascade="all, delete-orphan")


class Dimension(Base):
    __tablename__ = "dimensiones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cuestionario_versiones.id"), nullable=False
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(180), nullable=False)
    dominio: Mapped[str] = mapped_column(String(180), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)

    version: Mapped[CuestionarioVersion] = relationship(back_populates="dimensiones")
    preguntas: Mapped[list["Pregunta"]] = relationship(back_populates="dimension", cascade="all, delete-orphan")
    baremos: Mapped[list["Baremo"]] = relationship(back_populates="dimension", cascade="all, delete-orphan")
    recomendaciones: Mapped[list["Recomendacion"]] = relationship(back_populates="dimension", cascade="all, delete-orphan")


class Pregunta(Base):
    __tablename__ = "preguntas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dimensiones.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    inversa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    valor_minimo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valor_maximo: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    dimension: Mapped[Dimension] = relationship(back_populates="preguntas")


class Baremo(Base):
    __tablename__ = "baremos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dimensiones.id"), nullable=False)
    nivel: Mapped[str] = mapped_column(String(30), nullable=False)
    minimo: Mapped[float] = mapped_column(Float, nullable=False)
    maximo: Mapped[float] = mapped_column(Float, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)

    dimension: Mapped[Dimension] = relationship(back_populates="baremos")


class Recomendacion(Base):
    __tablename__ = "recomendaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dimensiones.id"), nullable=False)
    nivel: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    prioridad: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    dimension: Mapped[Dimension] = relationship(back_populates="recomendaciones")
