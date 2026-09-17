import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import utcnow
from app.db.base import Base


class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False
    )
    evaluador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cuestionario_versiones.id"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(180), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="BORRADOR", nullable=False)
    justificacion_cierre: Mapped[str | None] = mapped_column(Text)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    organizacion: Mapped["Organizacion"] = relationship(back_populates="evaluaciones")
    evaluador: Mapped["Usuario"] = relationship(foreign_keys=[evaluador_id])
    version: Mapped["CuestionarioVersion"] = relationship()
    participantes: Mapped[list["EvaluacionParticipante"]] = relationship(
        back_populates="evaluacion", cascade="all, delete-orphan"
    )
    informes: Mapped[list["Informe"]] = relationship(back_populates="evaluacion")


class EvaluacionParticipante(Base):
    __tablename__ = "evaluacion_participantes"
    __table_args__ = (UniqueConstraint("evaluacion_id", "trabajador_id", name="uq_eval_trabajador"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluaciones.id"), nullable=False
    )
    trabajador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    notificado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_notificacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="participantes")
    trabajador: Mapped["Usuario"] = relationship(foreign_keys=[trabajador_id])
    consentimiento: Mapped["Consentimiento | None"] = relationship(
        back_populates="participante", uselist=False
    )
    respuestas: Mapped[list["Respuesta"]] = relationship(back_populates="participante", cascade="all, delete-orphan")
    resultados: Mapped[list["ResultadoDimension"]] = relationship(back_populates="participante")


class Consentimiento(Base):
    __tablename__ = "consentimientos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluacion_participantes.id"), unique=True, nullable=False
    )
    trabajador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    aceptado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    texto_version: Mapped[str] = mapped_column(String(40), nullable=False)
    ip_origen: Mapped[str | None] = mapped_column(String(64))
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    participante: Mapped[EvaluacionParticipante] = relationship(back_populates="consentimiento")


class Respuesta(Base):
    __tablename__ = "respuestas"
    __table_args__ = (UniqueConstraint("participante_id", "pregunta_id", name="uq_respuesta_pregunta"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluacion_participantes.id"), nullable=False
    )
    pregunta_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("preguntas.id"), nullable=False)
    valor_cifrado: Mapped[str] = mapped_column(Text, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    participante: Mapped[EvaluacionParticipante] = relationship(back_populates="respuestas")
    pregunta: Mapped["Pregunta"] = relationship()


class ResultadoDimension(Base):
    __tablename__ = "resultados_dimension"
    __table_args__ = (UniqueConstraint("participante_id", "dimension_id", name="uq_resultado_dimension"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluacion_participantes.id"), nullable=False
    )
    dimension_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dimensiones.id"), nullable=False)
    puntaje_bruto: Mapped[float] = mapped_column(Float, nullable=False)
    puntaje_transformado: Mapped[float] = mapped_column(Float, nullable=False)
    nivel: Mapped[str] = mapped_column(String(30), nullable=False)
    calculado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    participante: Mapped[EvaluacionParticipante] = relationship(back_populates="resultados")
    dimension: Mapped["Dimension"] = relationship()


class Informe(Base):
    __tablename__ = "informes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluaciones.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)
    trabajador_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    area_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.id"))
    ruta_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    generado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    generado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    anonimizado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    evaluacion: Mapped[Evaluacion] = relationship(back_populates="informes")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    leida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evaluacion_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluaciones.id"))
    fecha_envio: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    fecha_lectura: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    usuario: Mapped["Usuario"] = relationship()
