import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import utcnow
from app.db.base import Base


class TicketSoporte(Base):
    """Mensaje enviado desde el formulario del Centro de ayuda."""

    __tablename__ = "tickets_soporte"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)  # PENDIENTE | RESUELTO
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    respuesta: Mapped[str | None] = mapped_column(Text, nullable=True)
    respondido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    usuario: Mapped["Usuario"] = relationship()
