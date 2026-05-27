"""
Repositorio para obtener la información de usuario asociada a un token de
verificación.
"""

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.shared.models.auth_model import Auth
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.verification_tokens_model import VerificationToken


class GetUserInfoRepository:
    """
    Encapsula las consultas necesarias para recuperar el contexto del usuario
    a partir de un token de verificación.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_token_context(self, token: UUID) -> VerificationToken | None:
        """
        Obtiene el token con sus relaciones cargadas para evitar consultas
        perezosas al construir la respuesta.
        """
        return (
            self.db.query(VerificationToken)
            .filter(VerificationToken.token == token)
            .options(
                joinedload(VerificationToken.auth).joinedload(Auth.profile),
                joinedload(VerificationToken.auth).joinedload(Auth.jids),
                joinedload(VerificationToken.auth).joinedload(
                    Auth.student_course_requests
                ),
                joinedload(VerificationToken.auth).joinedload(
                    Auth.teacher_course_requests
                ),
            )
            .one_or_none()
        )

    def get_course_request(
        self, auth_id: int
    ) -> StudentCourseRequest | TeacherCourseRequest | None:
        """
        Obtiene la solicitud de curso asociada a un usuario.

        Por lógica de negocio, solo debe existir una solicitud por usuario,
        independientemente de su rol. Si encontramos más de una, retornamos None
        para indicar inconsistencia.

        Args:
            auth_id: ID del usuario (Auth)

        Returns:
            La solicitud de curso (Student o Teacher) o None si no existe o hay múltiples
        """
        # Primero intentamos obtener solicitudes de alumno
        student_requests = (
            self.db.query(StudentCourseRequest)
            .filter(StudentCourseRequest.auth_id == auth_id)
            .all()
        )

        # Luego intentamos obtener solicitudes de docente
        teacher_requests = (
            self.db.query(TeacherCourseRequest)
            .filter(TeacherCourseRequest.auth_id == auth_id)
            .all()
        )

        # Validar que exista exactamente una solicitud en total
        total_requests = len(student_requests) + len(teacher_requests)
        if total_requests == 0:
            return None
        if total_requests > 1:
            # Inconsistencia: más de una solicitud
            return None

        # Retornar la única solicitud encontrada
        if student_requests:
            return student_requests[0]
        return teacher_requests[0]
