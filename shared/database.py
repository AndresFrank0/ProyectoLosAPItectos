# src/shared/database.py
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/elbuensabor")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Creates all database tables defined by SQLModel metadata."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency to get a database session."""
    with Session(engine) as session:
        yield session