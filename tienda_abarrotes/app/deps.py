import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    error = HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas o token expirado",
                          headers={"WWW-Authenticate": "Bearer"})
    try:
        username = decode_token(token).get("sub")
    except jwt.PyJWTError:
        raise error
    user = db.scalar(select(Usuario).where(Usuario.username == username))
    if user is None or not user.activo:
        raise error
    return user


def require_roles(*roles: str):
    """Autorización por rol: solo deja pasar a los roles indicados."""
    def checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permiso para esta operación")
        return user
    return checker


solo_admin = require_roles("admin")
admin_o_cajero = require_roles("admin", "cajero")
