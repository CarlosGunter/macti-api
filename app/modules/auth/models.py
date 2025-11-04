from typing import Optional
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


class AccountRequest(Base):
    __tablename__ = "account_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False)
    #
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.pending,
        nullable=False,
    )
    institute: Mapped[InstituteEnum] = mapped_column(
        Enum(InstituteEnum, name="institute_enum"), nullable=False
    )
    kc_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    moodle_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    validaciones: Mapped[list["MCT_Validacion"]] = relationship(
        "MCT_Validacion", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AccountRequest(email='{self.email}', status='{self.status.value}')>"


class MCT_Validacion(Base):
    __tablename__ = "MCT_Validacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("account_requests.id"), nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_expiracion: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    bandera: Mapped[int] = mapped_column(Integer, default=0)
    account: Mapped["AccountRequest"] = relationship(
        "AccountRequest", back_populates="validaciones"
    )

    def __repr__(self):
        return f"<EmailValidation(email='{self.email}', is_used={self.bandera})>"
