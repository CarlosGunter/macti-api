from app.core.database import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("¡Base de datos reseteada correctamente!")
