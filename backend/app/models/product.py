import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import utcnow
from app.db.base import Base


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    precio: Mapped[int] = mapped_column(Integer, nullable=False)
    imagen_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
