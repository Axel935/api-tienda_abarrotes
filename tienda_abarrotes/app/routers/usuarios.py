from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import solo_admin
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"], dependencies=[Depends(solo_admin)])


@router.post("", response_model=UsuarioOut, status_code=201)
def crear_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    return usuario_service.crear(db, data)


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.id)).all()


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(usuario_id: int, data: UsuarioUpdate, db: Session = Depends(get_db),
                       actual: Usuario = Depends(solo_admin)):
    return usuario_service.actualizar(db, usuario_id, data, actual)
