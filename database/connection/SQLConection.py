
from sqlmodel import Session, SQLModel, create_engine
from typing import Annotated
from fastapi import Depends
import os
from dotenv import load_dotenv

load_dotenv()

# Obtener la URL de la base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida en las variables de entorno")

# Configuración del engine para PostgreSQL
# Nota: "check_same_thread" es solo para SQLite, no se usa con PostgreSQL
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para ver las queries SQL en desarrollo
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_size=5,  # Tamaño del pool de conexiones
    max_overflow=10,  # Conexiones adicionales permitidas
)


def create_db_and_tables():
    """Crea las tablas en la base de datos si no existen."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Generador de sesiones para inyección de dependencias."""
    with Session(engine) as session:
        yield session


# Tipo anotado para usar como dependencia en FastAPI
SessionDep = Annotated[Session, Depends(get_session)]