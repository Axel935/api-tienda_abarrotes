from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import MovimientoInventario, Producto, Proveedor, Usuario
from app.schemas import AjusteStock, ProductoCreate, ProductoUpdate


def obtener(db: Session, producto_id: int) -> Producto:
    prod = db.get(Producto, producto_id)
    if prod is None:
        raise AppError("Producto no encontrado", 404)
    return prod


def _verificar_proveedor(db: Session, proveedor_id: int | None) -> None:
    if proveedor_id is not None:
        prov = db.get(Proveedor, proveedor_id)
        if prov is None or not prov.activo:
            raise AppError("El proveedor indicado no existe o está inactivo", 404)


def _codigo_libre(db: Session, codigo: str, excepto_id: int | None = None) -> None:
    existente = db.scalar(select(Producto).where(Producto.codigo == codigo))
    if existente and existente.id != excepto_id:
        raise AppError("Ya existe un producto con ese código", 409)


def listar(db: Session, buscar: str | None, solo_activos: bool, skip: int, limit: int):
    query = select(Producto)
    if solo_activos:
        query = query.where(Producto.activo.is_(True))
    if buscar:
        patron = f"%{buscar}%"
        query = query.where(Producto.nombre.ilike(patron) | Producto.codigo.ilike(patron))
    return db.scalars(query.order_by(Producto.nombre).offset(skip).limit(limit)).all()


def stock_bajo(db: Session):
    query = select(Producto).where(Producto.activo.is_(True), Producto.stock <= Producto.stock_minimo)
    return db.scalars(query.order_by(Producto.stock)).all()


def crear(db: Session, data: ProductoCreate, usuario: Usuario) -> Producto:
    _codigo_libre(db, data.codigo)
    _verificar_proveedor(db, data.proveedor_id)
    prod = Producto(**data.model_dump())
    db.add(prod)
    db.flush()
    if prod.stock > 0:
        db.add(MovimientoInventario(producto_id=prod.id, tipo="INVENTARIO_INICIAL",
                                    cantidad=prod.stock, referencia="alta de producto",
                                    usuario_id=usuario.id))
    db.commit()
    return prod


def actualizar(db: Session, producto_id: int, data: ProductoUpdate) -> Producto:
    prod = obtener(db, producto_id)
    cambios = data.model_dump(exclude_unset=True)
    if "codigo" in cambios:
        _codigo_libre(db, cambios["codigo"], prod.id)
    if "proveedor_id" in cambios:
        _verificar_proveedor(db, cambios["proveedor_id"])
    compra = cambios.get("precio_compra", prod.precio_compra)
    venta = cambios.get("precio_venta", prod.precio_venta)
    if venta < compra:
        raise AppError("El precio de venta no puede ser menor que el de compra", 422)
    for campo, valor in cambios.items():
        setattr(prod, campo, valor)
    db.commit()
    return prod


def desactivar(db: Session, producto_id: int) -> None:
    """Baja lógica: se conserva el historial de ventas y movimientos."""
    prod = obtener(db, producto_id)
    prod.activo = False
    db.commit()


def ajustar_stock(db: Session, producto_id: int, data: AjusteStock, usuario: Usuario) -> Producto:
    prod = obtener(db, producto_id)
    nuevo = prod.stock + data.cantidad
    if nuevo < 0:
        raise AppError(f"El ajuste dejaría el stock en {nuevo}; existencia actual: {prod.stock}", 409)
    prod.stock = nuevo
    db.add(MovimientoInventario(producto_id=prod.id, tipo="AJUSTE", cantidad=data.cantidad,
                                referencia=data.motivo, usuario_id=usuario.id))
    db.commit()
    return prod
