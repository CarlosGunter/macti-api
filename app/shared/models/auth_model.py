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

# TYPE_CHECKING evita importaciones circulares en tiempo de ejecución
if TYPE_CHECKING:
    from app.shared.models.JIDs_model import JIDs
    from app.shared.models.teacher_courses_model import TeacherCourseRequest
    from app.shared.models.user_profiles_model import UserProfile
    from app.shared.models.verification_tokens_model import VerificationToken


class Auth(Base):
    """
    Representación en base de datos de un usuario y su cuenta de autenticación.
    Tabla: MCT_auth (según imagen aprobada por el PM)
    """

    __tablename__ = "MCT_auth"

    # ========== IDENTIFICACIÓN PRIMARIA ==========
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ========== DATOS BÁSICOS DEL USUARIO ==========
    email: Mapped[EmailStr] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"), nullable=False
    )

    # ========== ESTADO DE LA CUENTA ==========
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
        back_populates="auth",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Relación 1:1 con JIDs (MCT_jids)
    # Almacena los identificadores externos (Keycloak, Moodle, Jupyter)
    jids: Mapped[Optional["JIDs"]] = relationship(
        "JIDs", back_populates="auth", uselist=False, cascade="all, delete-orphan"
    )

    # Relación 1:N con TeacherCourseRequest (MCT_teacher_courses)
    # Un usuario puede tener múltiples cursos solicitados
    assigned_courses: Mapped[list["TeacherCourseRequest"]] = relationship(
        "TeacherCourseRequest", back_populates="auth", cascade="all, delete-orphan"
    )

    # Relación 1:N con VerificationToken (MCT_verification_tokens)
    verification_tokens: Mapped[list["VerificationToken"]] = relationship(
        "VerificationToken", back_populates="auth", cascade="all, delete-orphan"
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
        return f"<Auth(email='{self.email}', is_active={self.is_active})>"
