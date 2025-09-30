from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime

class AccountRequest(Base):
    __tablename__ = "account_requests"
    # TODO: Instituto

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    course_id = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    kc_id = Column(String, nullable=True)
    moodle_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MCT_Validacion(Base):
    __tablename__ = "MCT_Validacion"
    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String, nullable=False, unique=True, index=True)
    token = Column(String, nullable=False, unique=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime, nullable=True)
    bandera = Column(Integer, default=0) 