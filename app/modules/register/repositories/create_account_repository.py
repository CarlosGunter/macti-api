"""
Repositorio para `CreateAccountController`.

Encapsula las consultas a la base de datos necesarias para el
flujo de aprovisionamiento de cuentas (Keycloak + Moodle).
"""
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.shared.models.auth_model import Auth
from app.shared.models.JIDs_model import JIDs
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.verification_tokens_model import VerificationToken
from app.shared.enums.status_enum import RequestStatusEnum


class CreateAccountRepository:
    """Encapsula consultas y operaciones de BD usadas por CreateAccountController."""

    def __init__(self, db: Session):
        self.db = db

    def get_auth_with_relations(self, auth_id: int) -> Optional[Auth]:
        """Obtiene el `Auth` con relaciones necesarias cargadas.

        Carga: `profile`, `jids`, `verification_tokens`, `teacher_course_requests`,
        `student_course_requests` para evitar lazy-loading durante el flujo.
        """
        return (
            self.db.query(Auth)
            .filter(Auth.id == auth_id)
            .options(
                joinedload(Auth.profile),
                joinedload(Auth.jids),
                joinedload(Auth.verification_tokens),
                joinedload(Auth.teacher_course_requests),
                joinedload(Auth.student_course_requests),
            )
            .one_or_none()
        )

    def get_pending_teacher_course(self, auth_id: int) -> Optional[TeacherCourseRequest]:
        """Retorna la solicitud de docente pendiente (si existe)."""
        return (
            self.db.query(TeacherCourseRequest)
            .filter(
                TeacherCourseRequest.auth_id == auth_id,
                TeacherCourseRequest.status == RequestStatusEnum.PENDING,
            )
            .first()
        )

    def get_pending_student_course(self, auth_id: int) -> Optional[StudentCourseRequest]:
        """Retorna la solicitud de alumno pendiente (si existe)."""
        return (
            self.db.query(StudentCourseRequest)
            .filter(
                StudentCourseRequest.auth_id == auth_id,
                StudentCourseRequest.status == RequestStatusEnum.PENDING,
            )
            .first()
        )

    def delete_verification_token(self, auth_id: int) -> None:
        """Elimina cualquier token de verificación asociado al `Auth`.

        No lanza si no hay token; la operación es idempotente.
        """
        token = (
            self.db.query(VerificationToken)
            .filter(VerificationToken.auth_id == auth_id)
            .first()
        )
        if token:
            self.db.delete(token)

    def ensure_jids(self, auth: Auth) -> JIDs:
        """Asegura que exista un registro `JIDs` para el `Auth` y lo retorna."""
        if auth.jids:
            return auth.jids

        jid = JIDs(auth_id=auth.id)
        self.db.add(jid)
        # No commit here; quien llama hará commit al final del flujo
        return jid
