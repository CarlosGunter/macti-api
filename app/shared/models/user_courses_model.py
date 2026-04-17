# Módulo UserCourses - Modelo de Relación Usuario-Curso
#
# Este modelo define la estructura de persistencia para los detalles específicos
# de los cursos vinculados a una cuenta de usuario.

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    from app.shared.models.users_model import UserAccounts


class UserCourses(Base):
    """
    Representación en base de datos de los detalles académicos de una solicitud.

    Almacena la información necesaria para el aprovisionamiento de espacios
    especialmente para el rol de docente.

    Relaciones:
        - Pertenece a un UserAccounts mediante auth_id
    """

    __tablename__ = "MCT_user_courses"

    # Identificador único del registro de detalle
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Relación con la cuenta de usuario principal (Foreign Key)
    auth_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_auth.id"), nullable=False
    )

    # Metadatos del curso solicitado
    course_full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    groups: Mapped[str | None] = mapped_column(String, nullable=True)

    # Estado de la solicitud para este curso específico
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    # Relación inversa hacia el modelo de cuentas de usuario
    user: Mapped["UserAccounts"] = relationship(
        "UserAccounts", back_populates="assigned_courses"
    )

    def __repr__(self):
        """Retorna una representación legible del objeto de curso por usuario."""
        return f"<UserCourse(course='{self.course_full_name}', status='{self.status.value}')>"
