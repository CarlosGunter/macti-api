"""Controlador para solicitudes de curso de estudiantes autenticados."""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.register.repositories.authenticated_student_request_repository import (
    AuthenticatedStudentRequestRepository,
)
from app.shared.dependecies.auth_current_user import CurrentUser
from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.student_courses_model import StudentCourseRequest

from ..schemas import AuthenticatedStudentRequestSchema


class AuthenticatedStudentRequestController:
    """Controlador que registra solicitudes de curso para alumnos autenticados."""

    @staticmethod
    async def request_student_course(
        data: AuthenticatedStudentRequestSchema,
        db: Session,
        user_info: CurrentUser,
    ) -> dict[str, str]:
        """Orquesta la creación de una solicitud de curso para un alumno autenticado."""
        repository = AuthenticatedStudentRequestRepository(db)
        auth = AuthenticatedStudentRequestController._get_auth_or_raise(
            repository=repository,
            user_info=user_info,
        )
        AuthenticatedStudentRequestController._validate_no_duplicate_course_request(
            repository=repository,
            auth=auth,
            course_id=data.course_id,
        )

        student_request = repository.create_student_request(
            auth_id=auth.id,
            course_id=data.course_id,
        )
        AuthenticatedStudentRequestController._persist_request_or_raise(
            repository=repository,
            student_request=student_request,
        )

        return {"message": "Solicitud de curso registrada correctamente."}

    @staticmethod
    def _get_auth_or_raise(
        repository: AuthenticatedStudentRequestRepository,
        user_info: CurrentUser,
    ) -> Auth:
        """Recupera el `Auth` asociado al usuario autenticado o retorna HTTP 404."""
        auth = repository.get_auth_with_relations(user_info.auth_id)

        if auth is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "USUARIO_NO_ENCONTRADO",
                    "message": "No se encontró el usuario autenticado en la base de datos.",
                },
            )

        return auth

    @staticmethod
    def _validate_no_duplicate_course_request(
        repository: AuthenticatedStudentRequestRepository,
        auth: Auth,
        course_id: int,
    ) -> None:
        """Valida que no exista una solicitud duplicada y que no esté ya inscrito."""
        # Validación 1: ¿Ya existe una solicitud para este curso e instituto?
        exists_duplicate_request = (
            repository.exists_student_request_for_course_and_institute(
                auth_id=auth.id,
                course_id=course_id,
                institute=auth.institute,
            )
        )

        if exists_duplicate_request:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "DUPLICADO",
                    "message": "Ya existe una solicitud para este curso e instituto.",
                },
            )

        # Validación 2 (NUEVA): ¿Ya está ENROLLED en este curso?
        for request in auth.student_course_requests:
            if (
                request.moodle_course_id == course_id
                and request.status == RequestStatusEnum.ENROLLED
            ):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "YA_INSCRITO",
                        "message": "Ya estás inscrito en este curso.",
                    },
                )

    @staticmethod
    def _persist_request_or_raise(
        repository: AuthenticatedStudentRequestRepository,
        student_request: StudentCourseRequest,
    ) -> None:
        """Persiste la solicitud y maneja errores de infraestructura de forma genérica."""
        try:
            repository.commit()
            repository.refresh(student_request)
        except SQLAlchemyError as exc:
            repository.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ERROR_INTERNO",
                    "message": "Ocurrió un error interno al procesar la solicitud.",
                },
            ) from exc
        except Exception as exc:
            repository.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ERROR_INTERNO",
                    "message": "Ocurrió un error interno al procesar la solicitud.",
                },
            ) from exc
