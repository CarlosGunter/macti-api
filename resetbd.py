# app/scripts/reset_db.py

from app.core.database import Base, engine
from app.modules.auth.models import AccountRequest, MCT_Validacion
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("¡Base de datos reseteada correctamente!")
