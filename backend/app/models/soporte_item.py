import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SoporteItem(Base):
    """Contenido editable del Centro de ayuda (lo administra el Super Administrador desde el Panel).

    seccion: guia_<ROL> | faq | glosario | riesgo | novedades | atencion
    """

    __tablename__ = "soporte_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seccion: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    titulo: Mapped[str | None] = mapped_column(String(200), nullable=True)  # las guías no llevan título
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
