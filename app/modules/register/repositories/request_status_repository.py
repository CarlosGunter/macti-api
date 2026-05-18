"""
Repositorio para gestionar las operaciones de base de datos relacionadas
con el ciclo de vida de las solicitudes de cuenta (cambios de estado).
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, joinedload

from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.verification_tokens_model import VerificationToken


class RequestStatusRepository:
    """
    Encapsula todas las operaciones de persistencia relacionadas con
    la actualización de estado de solicitudes de cuenta.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_course_request(
        self, request_id: int, role: AccountRoleEnum
    ) -> StudentCourseRequest | TeacherCourseRequest | None:
        """
        Obtiene una solicitud de curso específica (Student o Teacher) con
        todas sus relaciones cargadas.

        Args:
            request_id: ID de la solicitud de curso
            role: Rol del usuario (ALUMNO o DOCENTE)

        Returns:
            La solicitud de curso con auth, profile y jids relacionados, o None
        """
        if role == AccountRoleEnum.ALUMNO:
            return (
                self.db.query(StudentCourseRequest)
                .filter(StudentCourseRequest.id == request_id)
                .options(
                    joinedload(StudentCourseRequest.auth).joinedload(Auth.profile),
                    joinedload(StudentCourseRequest.auth).joinedload(Auth.jids),
                )
                .one_or_none()
            )
        elif role == AccountRoleEnum.DOCENTE:
            return (
                self.db.query(TeacherCourseRequest)
                .filter(TeacherCourseRequest.id == request_id)
                .options(
                    joinedload(TeacherCourseRequest.auth).joinedload(Auth.profile),
                    joinedload(TeacherCourseRequest.auth).joinedload(Auth.jids),
                )
                .one_or_none()
            )
        return None

    def update_request_status(
        self,
        course_request: StudentCourseRequest | TeacherCourseRequest,
        new_status: RequestStatusEnum,
    ) -> None:
        """
        Actualiza el estado de una solicitud de curso.

        Args:
            course_request: La solicitud de curso a actualizar
            new_status: El nuevo estado
        """
        course_request.status = new_status

    def delete_verification_tokens(self, auth_id: int) -> None:
        """
        Elimina todos los tokens de verificación asociados a un usuario.

        Args:
            auth_id: ID del usuario (Auth)
        """
        self.db.query(VerificationToken).filter(
            VerificationToken.auth_id == auth_id
        ).delete(synchronize_session=False)

    def create_or_update_verification_token(self, auth_id: int) -> UUID:
        """
        Crea o actualiza un token de verificación para un usuario.

        Args:
            auth_id: ID del usuario (Auth)

        Returns:
            El token generado
        """
        token = uuid4()
        timestamp_now = datetime.now()
        expiration_date = timestamp_now + timedelta(days=7)

        existing_token = (
            self.db.query(VerificationToken)
            .filter(VerificationToken.auth_id == auth_id)
            .one_or_none()
        )

        if existing_token:
            existing_token.token = token
            existing_token.created_at = timestamp_now
            existing_token.expires_at = expiration_date
            existing_token.is_used = False
        else:
            new_token = VerificationToken(
                auth_id=auth_id,
                token=token,
                created_at=timestamp_now,
                expires_at=expiration_date,
                is_used=False,
            )
            self.db.add(new_token)

        return token

    def commit(self) -> None:
        """Persiste todos los cambios en la base de datos."""
        self.db.commit()

    def rollback(self) -> None:
        """Revierte todos los cambios en la sesión."""
        self.db.rollback()

    def refresh(self, entity: StudentCourseRequest | TeacherCourseRequest) -> None:
        """
        Actualiza una entidad con los datos más recientes de la BD.

        Args:
            entity: La entidad a refrescar
        """
        self.db.refresh(entity)
