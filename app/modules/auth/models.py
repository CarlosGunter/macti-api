# Atendiendo los puntos de 4 - 6, agrego 'ForeignKey' para poder realizarlos y relationship
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

class AccountStatusEnum(enum.Enum):
    pending = "pending"
    approved = "approved" 
    rejected = "rejected"
    created = "created"

"""  
Hice el pull a Dev como me dijiste y se eliminó todo lo que hice de los campos institutos hjaja,
en fin solo lo pego del pasado que tenía.
"""
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

# Primero se crea account, aquí cap el curso

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
    institute: Mapped[InstituteEnum] = mapped_column(
        Enum(InstituteEnum, name="institute_enum"),
        nullable=False
    )

    kc_id = Column(String, nullable=True)
    moodle_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Atendiendo las petciones de los puntos 4 - 6 creo primero la relación Account en MT_Validación
    validaciones: Mapped[list["MCT_Validacion"]] = relationship(
        "MCT_Validacion",
        back_populates="account",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AccountRequest(email='{self.email}', status='{self.status.value}', institute='{self.institute.value if self.institute else None}')>"





class MCT_Validacion(Base):
    __tablename__ = "MCT_Validacion"

    id = Column(Integer, primary_key=True, index=True)
    # Se inserta el id de account, como me lo pediste punto 3 'insertar id account en mc_validacion'
    account_id = Column(Integer, ForeignKey("account_requests.id"), nullable=True)
    email = Column(String, nullable=False,  index=True)
    token = Column(String, nullable=False, unique=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime, nullable=True)
    bandera = Column(Integer, default=0)
    account: Mapped["AccountRequest"] = relationship(
        "AccountRequest",
        back_populates="validaciones"
    )

    def __repr__(self):
            return f"<EmailValidation(email='{self.email}', is_used={self.bandera})>"