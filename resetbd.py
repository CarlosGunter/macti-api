from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class MCT_Validacion(Base):
    __tablename__ = "MCT_Validacion"
    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String, nullable=False, unique=True, index=True)
    token = Column(String, nullable=False, unique=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime, nullable=True)
    bandera = Column(Integer, default=0)
engine = create_engine("sqlite:///macti.db", echo=True)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("MCT_Validacion eliminada y recreada correctamente. :V")
