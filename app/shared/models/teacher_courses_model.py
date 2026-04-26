# Módulo UserCourses - Modelo de Relación Usuario-Curso
#
# Este modelo define la estructura de persistencia para los detalles específicos
# de los cursos vinculados a una cuenta de usuario. Permite rastrear el
# nombre completo del curso, los grupos asignados y el estado de aprobación.

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    from app.shared.models.auth_model import Auth


class TeacherCourseRequest(Base):
    """
    Representación en base de datos de los detalles académicos de una solicitud.
    Almacena la información necesaria para el aprovisionamiento de espacios
    especialmente para el rol de docente.

    Tabla: MCT_teachers_courses (según imagen aprobada)
    """

    __tablename__ = "MCT_teachers_courses"

    # ========== IDENTIFICACIÓN PRIMARIA ==========
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ========== RELACIÓN CON USUARIO ==========
    # Foreign Key a MCT_auth.id
    auth_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_auth.id", ondelete="CASCADE"), nullable=False
    )

    # ========== METADATOS DEL CURSO ==========
    # Nombre completo del curso solicitado
    course_full_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # Grupos solicitados, almacenados como string separado por comas
    # Ejemplo: "G1,G2,G3"
    groups: Mapped[str | None] = mapped_column(String, nullable=True)

    # ========== ESTADO DE LA SOLICITUD ==========
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    # ========== RELACIÓN INVERSA ==========
    # Relación con Auth (antes UserAccounts)
    auth: Mapped["Auth"] = relationship("Auth", back_populates="assigned_courses")

    def __repr__(self):
        """Retorna una representación legible del objeto."""
        return f"<TeacherCourseRequest(course='{self.course_full_name}', status='{self.status.value}')>"
