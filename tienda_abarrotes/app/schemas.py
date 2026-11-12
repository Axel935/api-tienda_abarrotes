from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

Dinero = Annotated[Decimal, Field(max_digits=10, decimal_places=2)]


class Rol(str, Enum):
    admin = "admin"
    cajero = "cajero"


class MetodoPago(str, Enum):
    efectivo = "efectivo"
    tarjeta = "tarjeta"


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Autenticación y usuarios ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    nombre: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=72)
    rol: Rol = Rol.cajero


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    rol: Optional[Rol] = None
    activo: Optional[bool] = None


class UsuarioOut(OrmModel):
    id: int
    username: str
    nombre: str
    rol: str
    activo: bool


# ---------- Proveedores ----------
class ProveedorCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    telefono: Optional[str] = Field(default=None, pattern=r"^[0-9+\- ]{7,20}$")
    email: Optional[str] = Field(default=None, max_length=120,
                                 pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(default=None, pattern=r"^[0-9+\- ]{7,20}$")
    email: Optional[str] = Field(default=None, max_length=120,
                                 pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ProveedorOut(OrmModel):
    id: int
    nombre: str
    telefono: Optional[str]
    email: Optional[str]
    activo: bool


# ---------- Productos ----------
class ProductoCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=30)
    nombre: str = Field(min_length=1, max_length=100)
    precio_compra: Dinero = Field(ge=0)
    precio_venta: Dinero = Field(gt=0)
    stock: int = Field(default=0, ge=0, le=1_000_000)
    stock_minimo: int = Field(default=5, ge=0)
    proveedor_id: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def venta_no_menor_a_compra(self):
        if self.precio_venta < self.precio_compra:
            raise ValueError("precio_venta no puede ser menor que precio_compra")
        return self


class ProductoUpdate(BaseModel):
    """El stock no se edita aquí: solo cambia con ventas, compras o ajustes."""
    codigo: Optional[str] = Field(default=None, min_length=1, max_length=30)
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    precio_compra: Optional[Dinero] = Field(default=None, ge=0)
    precio_venta: Optional[Dinero] = Field(default=None, gt=0)
    stock_minimo: Optional[int] = Field(default=None, ge=0)
    proveedor_id: Optional[int] = Field(default=None, gt=0)


class ProductoOut(OrmModel):
    id: int
    codigo: str
    nombre: str
    precio_compra: Decimal
    precio_venta: Decimal
    stock: int
    stock_minimo: int
    activo: bool
    proveedor_id: Optional[int]


class AjusteStock(BaseModel):
    cantidad: int = Field(description="Positivo suma, negativo resta")
    motivo: str = Field(min_length=3, max_length=100)

    @model_validator(mode="after")
    def distinto_de_cero(self):
        if self.cantidad == 0:
            raise ValueError("cantidad no puede ser 0")
        return self


# ---------- Ventas ----------
class ItemVenta(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=1000)


class VentaCreate(BaseModel):
    metodo_pago: MetodoPago
    items: list[ItemVenta] = Field(min_length=1, max_length=100)


class DetalleVentaOut(OrmModel):
    producto_id: int
    producto_nombre: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaOut(OrmModel):
    id: int
    fecha: datetime
    total: Decimal
    estado: str
    metodo_pago: str
    usuario_id: int
    detalles: list[DetalleVentaOut]


# ---------- Compras ----------
class ItemCompra(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=100_000)
    costo_unitario: Dinero = Field(gt=0)


class CompraCreate(BaseModel):
    proveedor_id: int = Field(gt=0)
    items: list[ItemCompra] = Field(min_length=1, max_length=100)


class DetalleCompraOut(OrmModel):
    producto_id: int
    cantidad: int
    costo_unitario: Decimal
    subtotal: Decimal


class CompraOut(OrmModel):
    id: int
    fecha: datetime
    total: Decimal
    proveedor_id: int
    usuario_id: int
    detalles: list[DetalleCompraOut]


# ---------- Inventario ----------
class MovimientoOut(OrmModel):
    id: int
    fecha: datetime
    producto_id: int
    tipo: str
    cantidad: int
    referencia: Optional[str]
    usuario_id: int
