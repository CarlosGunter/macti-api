Instrucciones rápidas para Alembic (migraciones)

- Activar el entorno virtual del proyecto.

- Generar una revisión con autogeneración (detecta cambios en los modelos):

```bash
alembic revision --autogenerate -m "initial"
```

- Aplicar las migraciones a la BD:

```bash
alembic upgrade head
```

Notas:
- `alembic.ini` usa por defecto `sqlite:///macti.db`. Alembic lee la URL desde `app.core.database.SQLALCHEMY_DATABASE_URL`.
- El archivo `env.py` importa `app.shared.models` para registrar todas las definiciones de modelo antes de autogenerar.
