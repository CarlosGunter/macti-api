from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    pass
"""
Módulo de Modelos de Base de Datos - Proyecto MACTI
Estructura de Identidad (Usuarios) y Estructura Académica (Cursos)
"""


class UserAccounts(Base):
    """
    TABLA: MCT_user_accounts
    PROPÓSITO: Almacena únicamente la IDENTIDAD del usuario.

    Esta tabla es el 'perfil global'. Si un maestro solicita 10 cursos,
    aquí solo existirá UN registro con su nombre, email y llaves de acceso (Keycloak/Moodle).
    """

    __tablename__ = "MCT_user_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[EmailStr] = mapped_column(
        String, nullable=False, unique=True, index=True
    )

    """Rol global del usuario: ALUMNO o DOCENTE."""
    role: Mapped[AccountRoleEnum | None] = mapped_column(
        Enum(AccountRoleEnum, name="account_role_enum"), nullable=True
    )

    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"), nullable=False
    )

    """IDs Externos: kc_id para Keycloak y moodle_user_id para su perfil de usuario en Moodle."""
    kc_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    moodle_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    """Relación 1:N - Un usuario puede tener muchas solicitudes o cursos asignados."""
    assigned_courses: Mapped[list["UserCourses"]] = relationship(
        "UserCourses", back_populates="owner_user", cascade="all, delete-orphan"
    )


class UserCourses(Base):
    """
     TABLA: MCT_user_courses
     PROPÓSITO: Almacena la relación entre el USUARIO y sus CURSOS.

    Cada fila representa una solicitud específica o un curso ya creado en Moodle para un docente.
    """

    __tablename__ = "MCT_user_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    """Llave Foránea que conecta este curso con su dueño en UserAccounts."""
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_user_accounts.id"), nullable=False
    )

    """ID único del curso generado por Moodle (moodle_course_id)."""
    moodle_course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    course_full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    course_key: Mapped[str | None] = mapped_column(String, nullable=True)
    groups: Mapped[str | None] = mapped_column(String, nullable=True)

    """
    Estatus de la solicitud del curso:
    PENDING: Esperando aprobación del admin.
    APPROVED: El admin dio el visto bueno.
    CREATED: El curso ya existe físicamente en Moodle.
    """
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    """Relación inversa para acceder a los datos del maestro desde el curso."""
    owner_user: Mapped["UserAccounts"] = relationship(
        "UserAccounts", back_populates="assigned_courses"
    )
