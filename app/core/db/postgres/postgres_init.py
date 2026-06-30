from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.environment import environment


def init_postgres():
    """
    Inicializa la conexión a PostgreSQL utilizando SQLAlchemy.

    Returns:
        engine: El motor de conexión a la base de datos.
        SessionLocal: Un generador de sesiones para interactuar con la base de datos.
    """

    database_url = environment.DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL no está configurada para PostgreSQL.")

    engine = create_engine(database_url, echo=True)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)
