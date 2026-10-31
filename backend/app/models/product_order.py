import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.crypto import utcnow
from app.db.base import Base


class PedidoProducto(Base):
    __tablename__ = "pedidos_productos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    iva: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE")
    stock_reintegrado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    items: Mapped[list["PedidoProductoItem"]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
        order_by="PedidoProductoItem.creado_en",
    )
    pagos: Mapped[list["PagoPedidoProducto"]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
        order_by="PagoPedidoProducto.procesado_en",
    )


class PedidoProductoItem(Base):
    __tablename__ = "pedido_producto_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedidos_productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    producto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productos.id", ondelete="SET NULL"),
        nullable=True,
    )
    nombre_producto: Mapped[str] = mapped_column(String(120), nullable=False)
    precio_unitario: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    pedido: Mapped["PedidoProducto"] = relationship(back_populates="items")


class PagoPedidoProducto(Base):
    __tablename__ = "pagos_pedidos_productos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pedidos_productos.id", ondelete="CASCADE"),
        nullable=False,
    )
    metodo: Mapped[str] = mapped_column(String(30), nullable=False, default="wompi")
    referencia: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    monto: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE")
    wompi_transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    wompi_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    wompi_payment_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    banco: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ultimos_digitos: Mapped[str | None] = mapped_column(String(4), nullable=True)
    titular: Mapped[str | None] = mapped_column(String(150), nullable=True)
    mensaje_respuesta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    procesado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    pedido: Mapped["PedidoProducto"] = relationship(back_populates="pagos")
