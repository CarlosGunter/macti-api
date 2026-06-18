from sqlalchemy import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.db.postgres.postgres_init import init_postgres
from app.core.db.sqlite.sqlite_init import init_sqlite
from app.core.environment import environment

# Mapa de proveedores de base de datos a sus funciones de inicialización
MAP_DB = {
    "sqlite": init_sqlite,
    "postgres": init_postgres,
}


def db_engine_factory() -> tuple[Engine, sessionmaker[Session]]:
    """
    Factory para inicializar el motor de base de datos y la sesión según la configuración.
    Lee el proveedor de base de datos desde las variables de entorno y ejecuta la función correspondiente del mapa.
    """
    db_provider = environment.DB_PROVIDER.lower().strip()

    # Obtenemos la función de inicialización del mapa
    initializer = MAP_DB.get(db_provider)

    if not initializer:
        valid_providers = ", ".join(MAP_DB.keys())
        raise ValueError(
            f"Proveedor de BD '{db_provider}' no soportado. "
            f"Opciones válidas: {valid_providers}"
        )

    return initializer()


# La Base para los modelos se queda centralizada aquí
Base = declarative_base()
# Inicialización dinámica al cargar el módulo
engine, SessionLocal = db_engine_factory()


def get_db():
    """Dependencia para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
