from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import sys

from routers import product_r, branches_r, categories_r, brands_r, admin_r
from database.connection.SQLConection import create_db_and_tables

# Importar modelo Admin para que SQLModel lo registre
from database.models.admin import Admin  # noqa: F401
from sqlalchemy.exc import IntegrityError
import subprocess
from pathlib import Path

from core.logging import configure_logging
from core.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Evento de inicio: crea las tablas en la base de datos."""
    # En producción es mejor correr migraciones fuera del proceso web (ej: docker-entrypoint.py).
    # Para desarrollo/CI se puede habilitar con RUN_MIGRATIONS_ON_STARTUP=1.
    if settings.run_migrations_on_startup and os.getenv("ALEMBIC_RUN") != "1":
        cwd = Path(__file__).parent
        try:
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=cwd,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("Alembic migrations applied")
            else:
                logger.error(
                    "Alembic failed (code %s): %s",
                    result.returncode,
                    (result.stderr or result.stdout or "").strip(),
                )
        except Exception:
            logger.exception("Error running Alembic at startup")

    try:
        create_db_and_tables()
    except Exception:
        logger.exception("Error creating tables")
        raise

    logger.info("Backend ready")
    yield


app = FastAPI(
    title="Team Celular API",
    description="API para catálogo de productos de Team Celular",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas principales para el catálogo de productos
app.include_router(product_r.router, tags=["Products"], prefix="/products")
app.include_router(branches_r.router, tags=["Branches"], prefix="/branches")
app.include_router(categories_r.router, tags=["Categories"], prefix="/categories")
app.include_router(brands_r.router, tags=["Brands"], prefix="/brands")

# Rutas de administración
app.include_router(admin_r.router, tags=["Admin"], prefix="/admin")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.exception("Database integrity error")
    return JSONResponse(status_code=409, content={"detail": "Conflict"})


@app.get("/")
def read_root():
    return {"msg": "Welcome to Team Celular's API!"}


@app.get("/health")
def health_check():
    """Health check endpoint para Railway (no depende de DB)."""
    return {"status": "healthy"}


@app.get("/health/db")
def health_db_check():
    """Health check de base de datos."""
    from database.connection.SQLConection import engine as db_engine
    from sqlalchemy import text

    try:
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        from fastapi import Response

        return Response(
            content='{"status":"unhealthy","database":"disconnected"}',
            status_code=503,
            media_type="application/json",
        )
