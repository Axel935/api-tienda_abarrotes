from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import DetalleVenta, MovimientoInventario, Producto, Usuario, Venta
from app.schemas import VentaCreate

CENTAVOS = Decimal("0.01")


def crear_venta(db: Session, data: VentaCreate, usuario: Usuario) -> Venta:
    """Proceso central: valida, calcula el total y descuenta inventario en UNA transacción."""
    # 1) Agrupar renglones repetidos del mismo producto
    cantidades: dict[int, int] = {}
    for item in data.items:
        cantidades[item.producto_id] = cantidades.get(item.producto_id, 0) + item.cantidad

    productos = {p.id: p for p in db.scalars(select(Producto).where(Producto.id.in_(cantidades)))}

    # 2) Validar TODO antes de modificar algo
    for pid, cantidad in cantidades.items():
        prod = productos.get(pid)
        if prod is None:
            raise AppError(f"El producto {pid} no existe", 404)
        if not prod.activo:
            raise AppError(f"El producto '{prod.nombre}' no está disponible para venta", 409)
        if prod.stock < cantidad:
            raise AppError(f"Stock insuficiente de '{prod.nombre}': "
                           f"disponible {prod.stock}, solicitado {cantidad}", 409)

    # 3) Aplicar: crear venta, calcular importes, descontar stock, registrar movimientos
    venta = Venta(usuario_id=usuario.id, metodo_pago=data.metodo_pago.value,
                  estado="COMPLETADA", total=Decimal("0.00"))
    total = Decimal("0.00")
    for pid, cantidad in cantidades.items():
        prod = productos[pid]
        subtotal = (prod.precio_venta * cantidad).quantize(CENTAVOS)
        prod.stock -= cantidad
        venta.detalles.append(DetalleVenta(producto_id=pid, cantidad=cantidad,
                                           precio_unitario=prod.precio_venta, subtotal=subtotal))
        total += subtotal
    venta.total = total
    db.add(venta)
    db.flush()  # obtiene venta.id
    for pid, cantidad in cantidades.items():
        db.add(MovimientoInventario(producto_id=pid, tipo="SALIDA_VENTA", cantidad=-cantidad,
                                    referencia=f"VENTA-{venta.id}", usuario_id=usuario.id))
    db.commit()
    return venta


def cancelar_venta(db: Session, venta_id: int, usuario: Usuario) -> Venta:
    venta = db.get(Venta, venta_id)
    if venta is None:
        raise AppError("Venta no encontrada", 404)
    if venta.estado == "CANCELADA":
        raise AppError("La venta ya estaba cancelada", 409)
    for det in venta.detalles:
        det.producto.stock += det.cantidad
        db.add(MovimientoInventario(producto_id=det.producto_id, tipo="ENTRADA_CANCELACION",
                                    cantidad=det.cantidad, referencia=f"CANCELA-VENTA-{venta.id}",
                                    usuario_id=usuario.id))
    venta.estado = "CANCELADA"
    db.commit()
    return venta


def obtener(db: Session, venta_id: int) -> Venta:
    venta = db.get(Venta, venta_id)
    if venta is None:
        raise AppError("Venta no encontrada", 404)
    return venta


def listar(db: Session, skip: int, limit: int, estado: str | None):
    query = select(Venta)
    if estado:
        query = query.where(Venta.estado == estado.upper())
    return db.scalars(query.order_by(Venta.id.desc()).offset(skip).limit(limit)).all()
