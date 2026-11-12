from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import solo_admin
from app.models import Usuario
from app.schemas import CompraCreate, CompraOut
from app.services import compra_service

router = APIRouter(prefix="/compras", tags=["Compras a proveedores"])


@router.post("", response_model=CompraOut, status_code=201)
def registrar_compra(data: CompraCreate, db: Session = Depends(get_db),
                     usuario: Usuario = Depends(solo_admin)):
    return compra_service.registrar_compra(db, data, usuario)


@router.get("", response_model=list[CompraOut], dependencies=[Depends(solo_admin)])
def listar_compras(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                   db: Session = Depends(get_db)):
    return compra_service.listar(db, skip, limit)


@router.get("/{compra_id}", response_model=CompraOut, dependencies=[Depends(solo_admin)])
def obtener_compra(compra_id: int, db: Session = Depends(get_db)):
    return compra_service.obtener(db, compra_id)
