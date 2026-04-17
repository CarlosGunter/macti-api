# Módulo UserAccounts - Modelo de Identidad Central
#
# Este modelo es el corazón de la persistencia en MACTI. Se encarga de
# consolidar la identidad del usuario, vinculando sus datos locales con los
# identificadores únicos de Keycloak (IAM), Moodle (LMS) y Jupyter.

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import EmailStr
from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    from app.shared.models.user_courses_model import UserCourses
    from app.shared.models.user_profiles_model import UserProfile
    from app.shared.models.verification_tokens_model import VerificationToken


class UserAccounts(Base):
    __tablename__ = "MCT_auth"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[EmailStr] = mapped_column(String, nullable=False, index=True)

    role: Mapped[AccountRoleEnum | None] = mapped_column(
        Enum(AccountRoleEnum, name="account_role_enum"), nullable=True
    )

    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"), nullable=False
    )

    kc_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    moodle_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jupyter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    assigned_courses: Mapped[list["UserCourses"]] = relationship(
        "UserCourses", back_populates="user", cascade="all, delete-orphan"
    )

    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        "VerificationToken", back_populates="user", cascade="all, delete-orphan"
    )

    @validates("email")
    def email_must_be_lowercase(self, _k, value) -> str:
        return value.lower() if isinstance(value, str) else value

    def __repr__(self):
        return f"<UserAccount(email='{self.email}', status='{self.status.value}')>"
