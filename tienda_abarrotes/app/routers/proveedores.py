from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import admin_o_cajero, solo_admin
from app.models import Proveedor
from app.schemas import ProveedorCreate, ProveedorOut, ProveedorUpdate
from app.services import proveedor_service

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


@router.post("", response_model=ProveedorOut, status_code=201, dependencies=[Depends(solo_admin)])
def crear_proveedor(data: ProveedorCreate, db: Session = Depends(get_db)):
    return proveedor_service.crear(db, data)


@router.get("", response_model=list[ProveedorOut], dependencies=[Depends(admin_o_cajero)])
def listar_proveedores(db: Session = Depends(get_db)):
    return db.scalars(select(Proveedor).where(Proveedor.activo.is_(True)).order_by(Proveedor.nombre)).all()


@router.get("/{proveedor_id}", response_model=ProveedorOut, dependencies=[Depends(admin_o_cajero)])
def obtener_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    return proveedor_service.obtener(db, proveedor_id)


@router.put("/{proveedor_id}", response_model=ProveedorOut, dependencies=[Depends(solo_admin)])
def actualizar_proveedor(proveedor_id: int, data: ProveedorUpdate, db: Session = Depends(get_db)):
    return proveedor_service.actualizar(db, proveedor_id, data)


@router.delete("/{proveedor_id}", status_code=204, dependencies=[Depends(solo_admin)])
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    proveedor_service.desactivar(db, proveedor_id)
    return Response(status_code=204)
