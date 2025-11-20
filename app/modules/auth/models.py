from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.modules.auth.enums import AccountStatusEnum
from app.shared.enums.institutes_enum import InstitutesEnum


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
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )
    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"),
        nullable=False,
    )
    kc_id: Mapped[str | None] = mapped_column(String, nullable=True)
    moodle_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    validaciones: Mapped[list["MCTValidacion"]] = relationship(
        "MCTValidacion", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AccountRequest(email='{self.email}', status='{self.status.value}')>"


class MCTValidacion(Base):
    __tablename__ = "MCT_Validacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("account_requests.id"), nullable=True
    )
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_expiracion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bandera: Mapped[int] = mapped_column(Integer, default=0)
    account: Mapped["AccountRequest"] = relationship(
        "AccountRequest", back_populates="validaciones"
    )

    def __repr__(self):
        return f"<EmailValidation(email='{self.email}', is_used={self.bandera})>"
