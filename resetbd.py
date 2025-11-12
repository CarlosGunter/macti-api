from app.core.database import Base, engine

# En esta nueva versión me pide instalar lo de abajo para poder resetar la bd e hice unos cambios
# py -m pip install sqlalchemy

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("¡Base de datos reseteada correctamente!")
