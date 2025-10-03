from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime
from typing import Optional
#Cambie unas cosas de la bd así que ejecuten el resetbd.py
class AccountRequest(Base):
    __tablename__ = "account_requests"
    # TODO: Instituto

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True, unique=True)
    course_id = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False)
    kc_id = Column(String, nullable=True)
    moodle_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    def __repr__(self):
        return f"<AccountRequest(email='{self.email}', status='{self.status}')>"
    
class MCT_Validacion(Base):
    __tablename__ = "MCT_Validacion"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    token = Column(String, nullable=False, unique=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime, nullable=True)
    bandera = Column(Integer, default=0) 
    def __repr__(self):
        return f"<EmailValidation(email='{self.email}', is_used={self.bandera})>"