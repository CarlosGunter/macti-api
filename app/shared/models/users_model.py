# Módulo UserAccounts - Modelo de Identidad Central
#
# Este modelo es el corazón de la persistencia en MACTI. Se encarga de
# consolidar la identidad del usuario, vinculando sus datos locales con los
# identificadores únicos de Keycloak (IAM) y Moodle (LMS).

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import EmailStr, field_validator
from sqlalchemy import DateTime, Enum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum

from .user_courses_model import UserCourses

if TYPE_CHECKING:
    from app.shared.models.user_courses_model import UserCourses
    from app.shared.models.verification_tokens_model import VerificationToken


class UserAccounts(Base):
    """
    Representación en base de datos de un usuario y su estado de cuenta.

    Gestiona la información de perfil, el rol administrativo asignado y los
    metadatos de sincronización con servicios externos.
    """

    __tablename__ = "MCT_user_accounts"

    # Identificación primaria y datos de contacto
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[EmailStr] = mapped_column(String, nullable=False, index=True)

    # Lógica de negocio: Roles y Estados
    role: Mapped[AccountRoleEnum | None] = mapped_column(
        Enum(AccountRoleEnum, name="account_role_enum"), nullable=True
    )

    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    # Origen del usuario para arquitectura multi-instancia
    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"), nullable=False
    )

    # Identificadores de integración externa
    kc_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    moodle_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Auditoría
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relaciones de propiedad y ciclo de vida (Cascade)
    assigned_courses: Mapped[list["UserCourses"]] = relationship(
        "UserCourses", back_populates="owner_user", cascade="all, delete-orphan"
    )

    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        "VerificationToken", back_populates="account", cascade="all, delete-orphan"
    )

    @field_validator("email", mode="before")
    @classmethod
    def email_must_be_lowercase(cls, value: str) -> str:
        """Valida que el correo electrónico se almacene en minúsculas."""
        return value.lower() if isinstance(value, str) else value

    def __repr__(self):
        """Genera una cadena descriptiva para depuración y logs."""
        return f"<UserAccount(email='{self.email}', status='{self.status.value}')>"
