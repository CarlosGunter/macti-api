from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import DateTime, Enum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    from app.shared.models.verification_tokens_model import VerificationToken


class UserAccounts(Base):
    __tablename__ = "MCT_user_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[EmailStr] = mapped_column(String, nullable=False, index=True)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[AccountRoleEnum | None] = mapped_column(
        Enum(AccountRoleEnum, name="account_role_enum"), nullable=True
    )
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )
    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"),
        nullable=False,
    )
    kc_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    moodle_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relaciones
    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        "VerificationToken", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self):
        role_value = self.role.value if self.role else "None"
        return (
            f"<AccountRequest(email='{self.email}', role='{role_value}', "
            f"status='{self.status.value}')>"
        )
