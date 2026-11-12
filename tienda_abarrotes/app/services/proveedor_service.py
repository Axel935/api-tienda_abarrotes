from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import Proveedor
from app.schemas import ProveedorCreate, ProveedorUpdate


def obtener(db: Session, proveedor_id: int) -> Proveedor:
    prov = db.get(Proveedor, proveedor_id)
    if prov is None:
        raise AppError("Proveedor no encontrado", 404)
    return prov


def _nombre_libre(db: Session, nombre: str, excepto_id: int | None = None) -> None:
    existente = db.scalar(select(Proveedor).where(Proveedor.nombre == nombre))
    if existente and existente.id != excepto_id:
        raise AppError("Ya existe un proveedor con ese nombre", 409)


def crear(db: Session, data: ProveedorCreate) -> Proveedor:
    _nombre_libre(db, data.nombre)
    prov = Proveedor(**data.model_dump())
    db.add(prov)
    db.commit()
    return prov


def actualizar(db: Session, proveedor_id: int, data: ProveedorUpdate) -> Proveedor:
    prov = obtener(db, proveedor_id)
    cambios = data.model_dump(exclude_unset=True)
    if "nombre" in cambios:
        _nombre_libre(db, cambios["nombre"], prov.id)
    for campo, valor in cambios.items():
        setattr(prov, campo, valor)
    db.commit()
    return prov


def desactivar(db: Session, proveedor_id: int) -> None:
    prov = obtener(db, proveedor_id)
    prov.activo = False
    db.commit()
