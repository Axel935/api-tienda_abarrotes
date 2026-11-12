from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(100))
    rol: Mapped[str] = mapped_column(String(20), default="cajero")  # admin | cajero
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Proveedor(Base):
    __tablename__ = "proveedores"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Producto(Base):
    __tablename__ = "productos"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), index=True)
    precio_compra: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=5)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    proveedor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("proveedores.id"), nullable=True)


class Venta(Base):
    __tablename__ = "ventas"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=_ahora)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estado: Mapped[str] = mapped_column(String(20), default="COMPLETADA")  # COMPLETADA | CANCELADA
    metodo_pago: Mapped[str] = mapped_column(String(20))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    detalles: Mapped[list["DetalleVenta"]] = relationship(
        back_populates="venta", cascade="all, delete-orphan")


class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"
    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    venta: Mapped[Venta] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship()

    @property
    def producto_nombre(self) -> str:
        return self.producto.nombre


class Compra(Base):
    __tablename__ = "compras"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=_ahora)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    detalles: Mapped[list["DetalleCompra"]] = relationship(
        back_populates="compra", cascade="all, delete-orphan")


class DetalleCompra(Base):
    __tablename__ = "detalle_compras"
    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[int] = mapped_column(Integer)
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    compra: Mapped[Compra] = relationship(back_populates="detalles")


class MovimientoInventario(Base):
    """Bitácora de todo cambio de existencias (historial de transacciones)."""
    __tablename__ = "movimientos_inventario"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=_ahora)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(30))
    cantidad: Mapped[int] = mapped_column(Integer)  # positivo = entra, negativo = sale
    referencia: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
