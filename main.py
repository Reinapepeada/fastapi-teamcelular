from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from routers import product_r, branches_r, categories_r, brands_r, admin_r
from database.connection.SQLConection import create_db_and_tables
# Importar modelo Admin para que SQLModel lo registre
from database.models.admin import Admin  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Evento de inicio: crea las tablas en la base de datos."""
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




