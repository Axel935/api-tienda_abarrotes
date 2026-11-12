import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.core.database import Base, get_db
from app.core.seed import crear_admin_inicial
from app.main import app


@pytest.fixture()
def client():
    """BD SQLite en memoria, limpia en cada prueba."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as db:
        crear_admin_inicial(db)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client, username, password):
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def admin(client):
    return _login(client, ADMIN_USERNAME, ADMIN_PASSWORD)


@pytest.fixture()
def cajero(client, admin):
    r = client.post("/usuarios", headers=admin, json={
        "username": "caja1", "nombre": "Cajero Uno", "password": "Cajero1234", "rol": "cajero"})
    assert r.status_code == 201
    return _login(client, "caja1", "Cajero1234")


@pytest.fixture()
def producto(client, admin):
    r = client.post("/productos", headers=admin, json={
        "codigo": "REF-600", "nombre": "Refresco 600ml", "precio_compra": "10.00",
        "precio_venta": "15.50", "stock": 20, "stock_minimo": 5})
    assert r.status_code == 201
    return r.json()
