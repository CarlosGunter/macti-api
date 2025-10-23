from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
import enum

""" 
    Aquí están los insitutos y estados
"""
class AccountStatusEnum(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    created = "created"
#institutos, sizisi
class InstituteEnum(enum.Enum):
    principal = "principal"
    cuantico = "cuantico"
    ciencias = "ciencias"
    ingenieria = "ingenieria"
    encit = "encit"
    ier = "ier"
    enes_m = "enes_m"
    hpc = "hpc"
    igf = "igf"
    ene = "ene"

""" 
    Aquí creamos la cuenta ya con el id de Key Moodle
"""
class AccountRequest(Base):
    __tablename__ = "account_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    course_id = Column(Integer, nullable=False)
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.pending,
        nullable=False
    )
    # Instituto
    institute: Mapped[InstituteEnum] = mapped_column(
        Enum(InstituteEnum, name="institute_enum"),
        nullable=False
    )

    kc_id = Column(String, nullable=True)
    moodle_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AccountRequest(email='{self.email}', status='{self.status.value}', institute='{self.institute.value}')>"
""" 
    Aquí es cuando solicitamos la cuentas, 
"""
class MCT_Validacion(Base):
    __tablename__ = "MCT_Validacion"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False,  index=True)
    token = Column(String, nullable=False, unique=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime, nullable=True)
    bandera = Column(Integer, default=0)
    institute: Mapped[InstituteEnum] = mapped_column(
        Enum(InstituteEnum, name="institute_enum"),
        nullable=False
    )

    def __repr__(self):
        return f"<EmailValidation(email='{self.email}', is_used={self.bandera})>"
