"""Repositorio para solicitudes de nuevos cursos de docentes autenticados."""

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.teacher_courses_model import TeacherCourseRequest


class AuthenticatedTeacherRequestRepository:
    """Encapsula la persistencia del flujo de solicitud de curso autenticada para docentes."""

    def __init__(self, db: Session):
        """Inicializa el repositorio con la sesión activa de base de datos."""
        self.db = db

    def get_auth_with_relations(self, auth_id: int) -> Auth | None:
        """Obtiene el `Auth` con su perfil y solicitudes de curso cargadas."""
        return (
            self.db.query(Auth)
            .filter(Auth.id == auth_id)
            .options(joinedload(Auth.profile))
            .one_or_none()
        )

    def create_teacher_request(
        self,
        auth_id: int,
        course_full_name: str,
        groups: list[str],
    ) -> TeacherCourseRequest:
        """Crea una nueva solicitud de curso para un docente autenticado."""
        teacher_request = TeacherCourseRequest(
            auth_id=auth_id,
            course_full_name=course_full_name,
            groups=",".join(groups) if groups else "",
            status=RequestStatusEnum.PENDING,
        )
        self.db.add(teacher_request)
        return teacher_request

    def exists_teacher_request_for_course_and_institute(
        self,
        auth_id: int,
        course_full_name: str,
        institute: InstitutesEnum,
    ) -> bool:
        """Valida si ya existe una solicitud del usuario para el mismo curso e instituto."""
        normalized_course_name = course_full_name.strip().lower()

        request_id = (
            self.db.query(TeacherCourseRequest.id)
            .join(Auth, TeacherCourseRequest.auth_id == Auth.id)
            .filter(
                Auth.id == auth_id,
                Auth.institute == institute,
                func.lower(func.trim(TeacherCourseRequest.course_full_name))
                == normalized_course_name,
            )
            .one_or_none()
        )

        return request_id is not None

    def commit(self) -> None:
        """Persiste los cambios pendientes en la base de datos."""
        self.db.commit()

    def rollback(self) -> None:
        """Revierte la transacción activa."""
        self.db.rollback()

    def refresh(self, entity: TeacherCourseRequest) -> None:
        """Refresca la entidad desde la base de datos."""
        self.db.refresh(entity)
