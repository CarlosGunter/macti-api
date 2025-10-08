from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime
import enum

class AccountStatusEnum(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    created = "created"


class AccountRequest(Base):
    __tablename__ = "account_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True, unique=True)
    course_id = Column(Integer, nullable=False)

    status = Column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.pending,
        nullable=False
    )

    kc_id = Column(String, nullable=True)
    moodle_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AccountRequest(email='{self.email}', status='{self.status.value}')>"


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
