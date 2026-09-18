import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import utcnow
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import Usuario


class Compra(Base):
    __tablename__ = "compras"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=True)
    bateria_nombre: Mapped[str] = mapped_column(String(150), default="Batería de Riesgo Psicosocial", nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tarifa_unitario: Mapped[float] = mapped_column(Float, nullable=False, default=10000.0)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    iva: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="compras")
    pagos: Mapped[list["Pago"]] = relationship(back_populates="compra", cascade="all, delete-orphan")


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    compra_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("compras.id"), nullable=False)
    metodo: Mapped[str] = mapped_column(String(30), nullable=False)
    referencia: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="APROBADO")
    banco: Mapped[str | None] = mapped_column(String(80))
    ultimos_digitos: Mapped[str | None] = mapped_column(String(4))
    titular: Mapped[str | None] = mapped_column(String(150))
    mensaje_respuesta: Mapped[str | None] = mapped_column(String(255))
    procesado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    compra: Mapped[Compra] = relationship(back_populates="pagos")