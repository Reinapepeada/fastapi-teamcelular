
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from typing import Annotated
from fastapi import Depends
import os
from dotenv import load_dotenv

load_dotenv()
postgress_railway = os.getenv("DATABASE_URL")


# connect_args = {"check_same_thread": False}
# engine = create_engine(postgress_railway, connect_args=connect_args)
engine = create_engine(postgress_railway)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

# elimnar tabla de user
def drop_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    # dropea la tabla de hero, team
    with Session(engine) as session:
        session.exec(text('DROP TABLE IF EXISTS alembic_version'))
        # session.exec(text('DROP TABLE IF EXISTS team'))
        session.commit()