from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import Compra, DetalleCompra, MovimientoInventario, Producto, Proveedor, Usuario
from app.schemas import CompraCreate

CENTAVOS = Decimal("0.01")


def registrar_compra(db: Session, data: CompraCreate, usuario: Usuario) -> Compra:
    """Entrada de mercancía de un proveedor: suma existencias y registra movimientos."""
    prov = db.get(Proveedor, data.proveedor_id)
    if prov is None or not prov.activo:
        raise AppError("El proveedor no existe o está inactivo", 404)

    ids = {i.producto_id for i in data.items}
    productos = {p.id: p for p in db.scalars(select(Producto).where(Producto.id.in_(ids)))}
    for pid in ids:
        if pid not in productos:
            raise AppError(f"El producto {pid} no existe", 404)
        if not productos[pid].activo:
            raise AppError(f"El producto '{productos[pid].nombre}' está inactivo", 409)

    compra = Compra(proveedor_id=prov.id, usuario_id=usuario.id, total=Decimal("0.00"))
    total = Decimal("0.00")
    for item in data.items:
        subtotal = (item.costo_unitario * item.cantidad).quantize(CENTAVOS)
        productos[item.producto_id].stock += item.cantidad
        compra.detalles.append(DetalleCompra(producto_id=item.producto_id, cantidad=item.cantidad,
                                             costo_unitario=item.costo_unitario, subtotal=subtotal))
        total += subtotal
    compra.total = total
    db.add(compra)
    db.flush()
    for item in data.items:
        db.add(MovimientoInventario(producto_id=item.producto_id, tipo="ENTRADA_COMPRA",
                                    cantidad=item.cantidad, referencia=f"COMPRA-{compra.id}",
                                    usuario_id=usuario.id))
    db.commit()
    return compra


def obtener(db: Session, compra_id: int) -> Compra:
    compra = db.get(Compra, compra_id)
    if compra is None:
        raise AppError("Compra no encontrada", 404)
    return compra


def listar(db: Session, skip: int, limit: int):
    return db.scalars(select(Compra).order_by(Compra.id.desc()).offset(skip).limit(limit)).all()
