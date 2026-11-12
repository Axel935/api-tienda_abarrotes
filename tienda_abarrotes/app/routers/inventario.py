from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import solo_admin
from app.models import MovimientoInventario
from app.schemas import MovimientoOut

router = APIRouter(prefix="/inventario", tags=["Inventario"], dependencies=[Depends(solo_admin)])


@router.get("/movimientos", response_model=list[MovimientoOut])
def listar_movimientos(producto_id: int | None = Query(None, gt=0),
                       skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                       db: Session = Depends(get_db)):
    query = select(MovimientoInventario)
    if producto_id:
        query = query.where(MovimientoInventario.producto_id == producto_id)
    return db.scalars(query.order_by(MovimientoInventario.id.desc()).offset(skip).limit(limit)).all()
