from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (registra las tablas)
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import AppError
from app.core.seed import crear_admin_inicial
from app.routers import auth, compras, inventario, productos, proveedores, usuarios, ventas


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        crear_admin_inicial(db)
    yield


app = FastAPI(title="API Tienda de Abarrotes",
              description="Administración de productos, ventas, compras e inventario.",
              version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def manejar_app_error(_: Request, exc: AppError):
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


for r in (auth.router, usuarios.router, proveedores.router, productos.router,
          ventas.router, compras.router, inventario.router):
    app.include_router(r)

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/app", StaticFiles(directory=FRONTEND, html=True), name="frontend")


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/app/")
