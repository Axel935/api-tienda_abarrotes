from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import admin_o_cajero, solo_admin
from app.models import Usuario
from app.schemas import AjusteStock, ProductoCreate, ProductoOut, ProductoUpdate
from app.services import producto_service

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("", response_model=list[ProductoOut], dependencies=[Depends(admin_o_cajero)])
def listar_productos(buscar: str | None = None, solo_activos: bool = True,
                     skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                     db: Session = Depends(get_db)):
    return producto_service.listar(db, buscar, solo_activos, skip, limit)


# Debe declararse antes de "/{producto_id}" para que no se interprete como un id
@router.get("/stock-bajo", response_model=list[ProductoOut], dependencies=[Depends(solo_admin)])
def productos_con_stock_bajo(db: Session = Depends(get_db)):
    return producto_service.stock_bajo(db)


@router.post("", response_model=ProductoOut, status_code=201)
def crear_producto(data: ProductoCreate, db: Session = Depends(get_db),
                   usuario: Usuario = Depends(solo_admin)):
    return producto_service.crear(db, data, usuario)


@router.get("/{producto_id}", response_model=ProductoOut, dependencies=[Depends(admin_o_cajero)])
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    return producto_service.obtener(db, producto_id)


@router.put("/{producto_id}", response_model=ProductoOut, dependencies=[Depends(solo_admin)])
def actualizar_producto(producto_id: int, data: ProductoUpdate, db: Session = Depends(get_db)):
    return producto_service.actualizar(db, producto_id, data)


@router.delete("/{producto_id}", status_code=204, dependencies=[Depends(solo_admin)])
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto_service.desactivar(db, producto_id)
    return Response(status_code=204)


@router.post("/{producto_id}/ajuste-stock", response_model=ProductoOut)
def ajustar_stock(producto_id: int, data: AjusteStock, db: Session = Depends(get_db),
                  usuario: Usuario = Depends(solo_admin)):
    return producto_service.ajustar_stock(db, producto_id, data, usuario)
