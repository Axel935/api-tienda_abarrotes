from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioUpdate


def autenticar(db: Session, username: str, password: str) -> Usuario:
    user = db.scalar(select(Usuario).where(Usuario.username == username))
    # Mismo mensaje para usuario inexistente o contraseña mala (no revela cuál falló)
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("Usuario o contraseña incorrectos", 401)
    if not user.activo:
        raise AppError("Usuario desactivado", 403)
    return user


def crear(db: Session, data: UsuarioCreate) -> Usuario:
    if db.scalar(select(Usuario).where(Usuario.username == data.username)):
        raise AppError("El nombre de usuario ya existe", 409)
    user = Usuario(username=data.username, nombre=data.nombre,
                   password_hash=hash_password(data.password), rol=data.rol.value)
    db.add(user)
    db.commit()
    return user


def actualizar(db: Session, user_id: int, data: UsuarioUpdate, actual: Usuario) -> Usuario:
    user = db.get(Usuario, user_id)
    if user is None:
        raise AppError("Usuario no encontrado", 404)
    cambios = data.model_dump(exclude_unset=True)
    if user.id == actual.id and (cambios.get("activo") is False or
                                 ("rol" in cambios and cambios["rol"] != "admin")):
        raise AppError("No puedes desactivarte ni quitarte el rol de administrador", 409)
    for campo, valor in cambios.items():
        setattr(user, campo, getattr(valor, "value", valor))
    db.commit()
    return user
