# API Tienda de Abarrotes

API REST con **FastAPI + SQLAlchemy + SQLite** para administrar productos, proveedores, ventas,
compras e inventario de una tienda de abarrotes. Autenticación con JWT y autorización por roles
(`admin`, `cajero`).

## Requisitos
- Python 3.11+
- [Poetry](https://python-poetry.org/)

## Instalación y ejecución local
```bash
git clone <URL_DEL_REPOSITORIO>
cd tienda_abarrotes
poetry install
poetry run uvicorn app.main:app --reload
```
- Swagger UI: http://127.0.0.1:8000/docs
- Frontend de pruebas: http://127.0.0.1:8000/app/
- Usuario inicial: `admin` / `Admin12345` (cámbialo con las variables de `.env.example`).

Las tablas y el administrador se crean automáticamente al arrancar (archivo `abarrotes.db`).

## Pruebas automáticas
```bash
poetry run pytest -v
```

## Estructura
```
app/
  main.py            # creación de la app, CORS, manejo de errores, routers
  models.py          # tablas (SQLAlchemy)
  schemas.py         # validación de entrada/salida (Pydantic)
  deps.py            # autenticación JWT y autorización por rol
  core/              # config, base de datos, seguridad, excepciones, seed
  routers/           # endpoints HTTP (capa de presentación)
  services/          # lógica de negocio
tests/               # pruebas con pytest
frontend/index.html  # cliente de pruebas
```

## Flujo rápido en Swagger
1. `POST /auth/login` con admin → copiar `access_token` → botón **Authorize**.
2. `POST /proveedores`, `POST /productos` (con stock inicial).
3. `POST /ventas` → verificar que baja el stock con `GET /productos/{id}`.
4. `GET /inventario/movimientos` para ver el historial.
