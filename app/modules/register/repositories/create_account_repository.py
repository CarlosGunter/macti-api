# Módulo CreateAccountRepository - Persistencia de Aprovisionamiento
#
# Encapsula las consultas a la base de datos necesarias para el
# flujo de aprovisionamiento de cuentas (Keycloak + Moodle).

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.JIDs_model import JIDs
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.verification_tokens_model import VerificationToken


class CreateAccountRepository:
    """Encapsula consultas y operaciones de BD usadas por CreateAccountController."""

    def __init__(self, db: Session):
        self.db = db

    def get_auth_with_relations(self, auth_id: int) -> Auth | None:
        """Obtiene el `Auth` con relaciones necesarias cargadas.

        Carga: `profile`, `jids`, `verification_token`, `teacher_course_requests`,
        `student_course_requests` para evitar lazy-loading durante el flujo.
        """
        return (
            self.db.query(Auth)
            .filter(Auth.id == auth_id)
            .options(
                joinedload(Auth.profile),
                joinedload(Auth.jids),
                joinedload(Auth.verification_token),
                joinedload(Auth.teacher_course_requests),
                joinedload(Auth.student_course_requests),
            )
            .one_or_none()
        )

    # Función para activar la cuenta de un usuario una vez que se aprueba su solicitud.
    # Cambia el campo `is_active` a True.
    def activate_auth_account(self, auth_id: int) -> Auth | None:
        """Busca el registro Auth por id y cambia su bandera `is_active` a True.

        Retorna la instancia modificada o None si el usuario no existe.
        """
        auth = self.db.query(Auth).filter(Auth.id == auth_id).one_or_none()
        if auth:
            auth.is_active = True
        return auth

    def get_approved_teacher_course(self, auth_id: int) -> TeacherCourseRequest | None:
        """Retorna la solicitud de docente aprobada (si existe)."""
        return (
            self.db.query(TeacherCourseRequest)
            .filter(
                TeacherCourseRequest.auth_id == auth_id,
                TeacherCourseRequest.status == RequestStatusEnum.APPROVED,
            )
            .one_or_none()
        )

    def get_approved_student_course(self, auth_id: int) -> StudentCourseRequest | None:
        """Retorna la solicitud de alumno aprobada (si existe)."""
        return (
            self.db.query(StudentCourseRequest)
            .filter(
                StudentCourseRequest.auth_id == auth_id,
                StudentCourseRequest.status == RequestStatusEnum.APPROVED,
            )
            .one_or_none()
        )

    def delete_verification_token(self, auth_id: int) -> None:
        """Elimina cualquier token de verificación asociado al `Auth`.

        No lanza si no hay token; la operación es idempotente.
        """
        token = (
            self.db.query(VerificationToken)
            .filter(VerificationToken.auth_id == auth_id)
            .one_or_none()
        )
        if token:
            self.db.delete(token)

    def save_jids(self, auth_id: int, kc_id: UUID, moodle_id: int) -> JIDs:
        """Crea o actualiza el registro de JIDs para el `Auth` dado."""
        jids = self.db.query(JIDs).filter(JIDs.auth_id == auth_id).one_or_none()
        if jids:
            jids.kc_id = kc_id
            jids.moodle_id = moodle_id
        else:
            jids = JIDs(auth_id=auth_id, kc_id=kc_id, moodle_id=moodle_id)
            self.db.add(jids)
        return jids

    def commit(self) -> None:
        """Persiste los cambios en la base de datos."""
        self.db.commit()

    def rollback(self) -> None:
        """Revierte la transacción actual."""
        self.db.rollback()

    def refresh(self, instance: object) -> None:
        """Refresca una instancia desde la base de datos."""
        self.db.refresh(instance)
