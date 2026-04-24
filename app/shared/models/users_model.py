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

# TYPE_CHECKING evita importaciones circulares en tiempo de ejecución
if TYPE_CHECKING:
    from app.shared.models.user_courses_model import UserCourses
    from app.shared.models.user_profiles_model import UserProfile
    from app.shared.models.verification_tokens_model import VerificationToken


class UserAccounts(Base):
    """
    Representación en base de datos de un usuario y su cuenta de autenticación.
    Tabla: MCT_auth (según imagen aprobada por el PM)
    """

    __tablename__ = "MCT_auth"

    # ========== IDENTIFICACIÓN PRIMARIA ==========
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ========== DATOS BÁSICOS DEL USUARIO ==========
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[EmailStr] = mapped_column(String, nullable=False, index=True)

    # ========== ROL DEL USUARIO (Enum) ==========
    # ALUMNO o DOCENTE
    role: Mapped[AccountRoleEnum | None] = mapped_column(
        Enum(AccountRoleEnum, name="account_role_enum"), nullable=True
    )

    # ========== ESTADO DE LA CUENTA ==========
    # PENDING -> APPROVED -> CREATED / REJECTED
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    # ========== INSTITUCIÓN DE PROCEDENCIA ==========
    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"), nullable=False
    )

    # ========== IDENTIFICADORES DE INTEGRACIÓN EXTERNA ==========
    # kc_id: UUID de Keycloak (guardado como string por compatibilidad con SQLite)
    kc_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # moodle_id: ID numérico del usuario en Moodle
    moodle_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # jupyter_id: ID en Jupyter Hub
    jupyter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # course_id: Curso asociado (para alumnos) o creado (para docentes)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # is_active: Si la cuenta está activa
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ========== AUDITORÍA ==========
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ========== RELACIONES CON OTRAS TABLAS ==========

    # Relación 1:1 con UserProfile (MCT_user_profiles)
    # uselist=False indica que es una relación uno a uno
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # Relación 1:N con UserCourses (MCT_user_courses)
    # Un usuario puede tener múltiples cursos solicitados
    assigned_courses: Mapped[list["UserCourses"]] = relationship(
        "UserCourses", back_populates="user", cascade="all, delete-orphan"
    )

    # Relación 1:N con VerificationToken (MCT_verification_tokens)
    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        "VerificationToken", back_populates="user", cascade="all, delete-orphan"
    )

    @validates("email")
    def email_must_be_lowercase(self, _k, value) -> str:
        """
        Valida que el correo electrónico se almacene siempre en minúsculas.
        Esto evita duplicados por diferencias de capitalización.
        """
        return value.lower() if isinstance(value, str) else value

    def __repr__(self):
        """Representación legible del objeto para depuración y logs."""
        return f"<UserAccount(email='{self.email}', status='{self.status.value}')>"
