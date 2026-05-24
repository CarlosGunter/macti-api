"""Repositorio para solicitudes de curso de estudiantes autenticados."""

from sqlalchemy.orm import Session, joinedload

from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.student_courses_model import StudentCourseRequest


class AuthenticatedStudentRequestRepository:
    """Encapsula la persistencia del flujo de solicitud de curso autenticada."""

    def __init__(self, db: Session):
        """Inicializa el repositorio con la sesión activa de base de datos."""
        self.db = db

    def get_auth_with_relations(self, auth_id: int) -> Auth | None:
        """Obtiene el `Auth` con su perfil y solicitudes de curso cargadas."""
        return (
            self.db.query(Auth)
            .filter(Auth.id == auth_id)
            .options(
                joinedload(Auth.profile),
                joinedload(Auth.student_course_requests),
                joinedload(Auth.teacher_course_requests),
            )
            .one_or_none()
        )

    def create_student_request(
        self, auth_id: int, course_id: int
    ) -> StudentCourseRequest:
        """Crea una nueva solicitud de curso para un alumno autenticado."""
        student_request = StudentCourseRequest(
            auth_id=auth_id,
            moodle_course_id=course_id,
            status=RequestStatusEnum.PENDING,
        )
        self.db.add(student_request)
        return student_request

    def exists_student_request_for_course_and_institute(
        self,
        auth_id: int,
        course_id: int,
        institute: InstitutesEnum,
    ) -> bool:
        """Valida si ya existe una solicitud del usuario para el mismo curso e instituto."""
        request_id = (
            self.db.query(StudentCourseRequest.id)
            .join(Auth, StudentCourseRequest.auth_id == Auth.id)
            .filter(
                Auth.id == auth_id,
                Auth.institute == institute,
                StudentCourseRequest.moodle_course_id == course_id,
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

    def refresh(self, entity: StudentCourseRequest) -> None:
        """Refresca la entidad desde la base de datos."""
        self.db.refresh(entity)
