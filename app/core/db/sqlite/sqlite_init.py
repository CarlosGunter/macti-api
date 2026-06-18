import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.environment import environment

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
DEFAULT_SQLITE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'macti.db')}"


def init_sqlite():
    """
    Inicializa la conexión a SQLite utilizando SQLAlchemy.
    Returns:
        engine: El motor de conexión a la base de datos.
        SessionLocal: Un generador de sesiones para interactuar con la base de datos.
    """

    database_url = environment.DATABASE_URL or DEFAULT_SQLITE_URL
    engine = create_engine(
        database_url, connect_args={"check_same_thread": False}, echo=True
    )
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)
