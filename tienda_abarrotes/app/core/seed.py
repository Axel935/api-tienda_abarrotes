from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.core.security import hash_password
from app.models import Usuario


def crear_admin_inicial(db: Session) -> None:
    """Crea el usuario administrador si todavía no existe."""
    if db.scalar(select(Usuario).where(Usuario.username == ADMIN_USERNAME)) is None:
        db.add(Usuario(username=ADMIN_USERNAME, nombre="Administrador",
                       password_hash=hash_password(ADMIN_PASSWORD), rol="admin"))
        db.commit()
