import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, deferred, mapped_column

from app.core.crypto import utcnow
from app.db.base import Base


class SoporteDocumento(Base):
    """Documento descargable del Centro de ayuda (lo sube el Super Administrador desde el Panel).

    El archivo se guarda en la base de datos (así sobrevive a los despliegues y entra en los respaldos).
    La columna `contenido` es diferida: no se carga al listar, solo al descargar.
    """

    __tablename__ = "soporte_documentos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nombre_archivo: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_mime: Mapped[str] = mapped_column(String(120), nullable=False)
    tamano: Mapped[int] = mapped_column(Integer, nullable=False)
    contenido: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
