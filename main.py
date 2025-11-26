from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from routers import product_r, branches_r, categories_r, brands_r, admin_r
from database.connection.SQLConection import create_db_and_tables
# Importar modelo Admin para que SQLModel lo registre
from database.models.admin import Admin  # noqa: F401
import subprocess
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Evento de inicio: crea las tablas en la base de datos."""
    # Ejecutar migraciones Alembic (si alembic está disponible)
    try:
        # Ejecutar en el directorio del proyecto para que alembic encuentre alembic.ini
        cwd = Path(__file__).parent
        result = subprocess.run(["alembic", "upgrade", "head"], cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Migraciones Alembic aplicadas correctamente")
        else:
            # Mostrar advertencia y continuar (creación de tablas fallback más abajo)
            print(f"⚠️ Advertencia migraciones: {result.stderr}")
    except FileNotFoundError:
        print("⚠️ Alembic no encontrado en el entorno, saltando migraciones automáticas")
    except Exception as e:
        print(f"⚠️ Error ejecutando migraciones automáticas: {e}")

    # Crear tablas si aún es necesario (fallback)
    create_db_and_tables()
    yield


app = FastAPI(
    title="Team Celular API",
    description="API para catálogo de productos de Team Celular",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar los orígenes permitidos
# En producción, usa la variable de entorno ALLOWED_ORIGINS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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


@app.get("/")
def read_root():
    return {"msg": "Welcome to Team Celular's API!"}


@app.get("/health")
def health_check():
    """Health check endpoint para Railway."""
    return {"status": "healthy"}




