import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import utcnow
from app.db.base import Base


class Organizacion(Base):
    __tablename__ = "organizaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(180), nullable=False)
    nit: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    sector: Mapped[str | None] = mapped_column(String(80))
    municipio: Mapped[str | None] = mapped_column(String(80))
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(180))
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    areas: Mapped[list["Area"]] = relationship(back_populates="organizacion")
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="organizacion")
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(back_populates="organizacion")


class Area(Base):
    __tablename__ = "areas"
    __table_args__ = (UniqueConstraint("organizacion_id", "nombre", name="uq_area_org_nombre"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    organizacion: Mapped[Organizacion] = relationship(back_populates="areas")
    trabajadores: Mapped[list["Usuario"]] = relationship(back_populates="area")
