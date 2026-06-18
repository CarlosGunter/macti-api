import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Añadir la raíz del proyecto al path para poder importar `app`
current_file = Path(__file__).resolve()
project_root = None
for parent in current_file.parents:
    if (parent / "app").is_dir():
        project_root = parent
        break

if project_root is None:
    project_root = current_file.parents[4]

project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

from app.core.environment import environment  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging if present.
if config.config_file_name:
    fileConfig(config.config_file_name)

# Import la configuración y la metadata de la aplicación
import app.shared.models  # noqa: F401,E402  # importar modelos para registrarlos
from app.core.db.database import Base  # noqa: E402

target_metadata = Base.metadata


def _get_db_provider() -> str:
    """Detecta el proveedor de base de datos desde el entorno."""
    # Intentamos leer la variable directamente del entorno o del objeto environment si está mapeada
    # Ajusta 'DB_PROVIDER' si tu objeto environment usa otro nombre de atributo
    provider = environment.DB_PROVIDER
    return str(provider).lower().strip()


def run_migrations_offline():
    """Run migrations in "offline" mode."""
    url = environment.DATABASE_URL
    db_provider = _get_db_provider()

    # Si estamos en SQLite, habilitamos render_as_batch
    is_sqlite = db_provider == "sqlite" or "sqlite" in url

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in "online" mode."""
    # Ensure Alembic knows the SQLAlchemy URL de forma dinámica
    config.set_main_option("sqlalchemy.url", environment.DATABASE_URL)
    configuration = config.get_section(config.config_ini_section) or {}

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    db_provider = _get_db_provider()
    url = environment.DATABASE_URL

    # Validaciones dinámicas basadas en el proveedor actual
    is_postgres = db_provider in ("postgres", "postgresql") or "postgres" in url
    is_sqlite = db_provider == "sqlite" or "sqlite" in url

    with connectable.connect() as connection:
        # Configuramos el contexto adaptativo de Alembic
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            # 1. Habilitamos Batch Mode únicamente si es SQLite para evitar Alter Tables rotos.
            # En Postgres se mantiene en False para usar migraciones estándar nativas.
            render_as_batch=is_sqlite,
            # 2. Control estricto de ENUMS nativos:
            # Si el proveedor es Postgres, le permitimos a Alembic gestionar tipos creados por el usuario.
            # Si caemos a SQLite, le indicamos que no intente emitir sentencias de tipos nativos.
            as_sql=False,
            template_args={"as_enum": is_postgres},
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
