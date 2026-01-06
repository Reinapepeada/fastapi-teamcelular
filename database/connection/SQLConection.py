
from sqlmodel import Session, SQLModel, create_engine
from typing import Annotated
from fastapi import Depends, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()


def _get_database_url() -> str | None:
    """Obtiene y normaliza la URL de base de datos si existe."""
    db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

    if not db_url:
        return None

    # Railway puede usar postgres:// pero SQLAlchemy necesita postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return db_url


DATABASE_URL = _get_database_url()

# Configuración del engine para PostgreSQL
# Nota: "check_same_thread" es solo para SQLite, no se usa con PostgreSQL
engine = None
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Cambiar a True para ver las queries SQL en desarrollo
        pool_pre_ping=True,  # Verifica la conexión antes de usarla
        pool_size=5,  # Tamaño del pool de conexiones
        max_overflow=10,  # Conexiones adicionales permitidas
    )
else:
    print("⚠️  DATABASE_URL/POSTGRES_URL no configurada. La API iniciará en modo sin base de datos.")


def create_db_and_tables():
    """Crea las tablas en la base de datos si no existen."""
    if engine is None:
        print("⏭️  Saltando create_all(): base de datos no configurada")
        return

    # In production with PostgreSQL we rely on Alembic migrations to create types
    # and tables. Calling SQLModel.metadata.create_all() can attempt to create
    # PostgreSQL enum types and raise DuplicateObject errors when types already
    # exist. Skip create_all for Postgres by default; allow override with
    # FORCE_CREATE_ALL=1 environment variable for development/testing.
    force = os.getenv("FORCE_CREATE_ALL", "0")
    if engine.url.drivername.startswith("postgresql") and force != "1":
        print("Skipping create_all() on PostgreSQL; use Alembic migrations instead")
        return

    SQLModel.metadata.create_all(engine)


def get_session():
    """Generador de sesiones para inyección de dependencias."""
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="La base de datos no está configurada o no es accesible",
        )

    with Session(engine) as session:
        yield session


# Tipo anotado para usar como dependencia en FastAPI
SessionDep = Annotated[Session, Depends(get_session)]
