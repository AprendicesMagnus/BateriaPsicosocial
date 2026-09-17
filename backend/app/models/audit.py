import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import utcnow
from app.db.base import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    accion: Mapped[str] = mapped_column(String(80), nullable=False)
    entidad: Mapped[str | None] = mapped_column(String(80))
    entidad_id: Mapped[str | None] = mapped_column(String(64))
    ip_origen: Mapped[str | None] = mapped_column(String(64))
    detalle: Mapped[dict | None] = mapped_column(JSONB)
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    nota: Mapped[str | None] = mapped_column(Text)
