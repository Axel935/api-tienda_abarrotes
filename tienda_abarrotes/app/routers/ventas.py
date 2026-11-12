from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import admin_o_cajero, solo_admin
from app.models import Usuario
from app.schemas import VentaCreate, VentaOut
from app.services import venta_service

router = APIRouter(prefix="/ventas", tags=["Ventas"])


@router.post("", response_model=VentaOut, status_code=201)
def registrar_venta(data: VentaCreate, db: Session = Depends(get_db),
                    usuario: Usuario = Depends(admin_o_cajero)):
    return venta_service.crear_venta(db, data, usuario)


@router.get("", response_model=list[VentaOut], dependencies=[Depends(admin_o_cajero)])
def listar_ventas(estado: str | None = Query(None, pattern="^(completada|cancelada)$"),
                  skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                  db: Session = Depends(get_db)):
    return venta_service.listar(db, skip, limit, estado)


@router.get("/{venta_id}", response_model=VentaOut, dependencies=[Depends(admin_o_cajero)])
def obtener_venta(venta_id: int, db: Session = Depends(get_db)):
    return venta_service.obtener(db, venta_id)


@router.post("/{venta_id}/cancelar", response_model=VentaOut)
def cancelar_venta(venta_id: int, db: Session = Depends(get_db),
                   usuario: Usuario = Depends(solo_admin)):
    return venta_service.cancelar_venta(db, venta_id, usuario)
