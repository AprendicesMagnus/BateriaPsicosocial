import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlanBateria(Base):
    """Plan informativo: rango de baterías y precio por batería. Lo administra el Super Administrador."""

    __tablename__ = "planes_baterias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    cantidad_min: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_max: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = "en adelante"
    precio_unitario: Mapped[int] = mapped_column(Integer, nullable=False)  # pesos colombianos por batería
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
