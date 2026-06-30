from sqlalchemy.orm import Session

from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest


class EnrollmentStatusRepository:
    """
    Pequeño repositorio debajo del caso de uso enroll_user.
    Responsabilidad exclusiva: cambiar el status de la solicitud a ENROLLED.
    Solo se ejecuta si la inscripción en Moodle fue exitosa.
    """

    def __init__(self, db: Session):
        self.db = db

    def mark_as_enrolled(
        self,
        request_course_data: StudentCourseRequest | TeacherCourseRequest,
    ) -> bool:
        """
        Actualiza el status a ENROLLED en la solicitud correspondiente.

        Args:
            request_course_data: La solicitud de curso (Student o Teacher)

        Returns:
            True si se actualizó correctamente
        """
        request_course_data.status = RequestStatusEnum.ENROLLED
        self.db.commit()
        self.db.refresh(request_course_data)
        return True
