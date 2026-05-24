"""Controlador para solicitudes de nuevos cursos de docentes autenticados."""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.register.repositories.authenticated_teacher_request_repository import (
    AuthenticatedTeacherRequestRepository,
)
from app.shared.dependecies.get_current_user import CurrentUserReturn
from app.shared.models.auth_model import Auth
from app.shared.models.teacher_courses_model import TeacherCourseRequest

from ..schemas import AuthenticatedTeacherRequestSchema


class AuthenticatedTeacherRequestController:
    """Controlador que registra solicitudes de nuevos cursos para docentes autenticados."""

    @staticmethod
    async def request_teacher_course(
        data: AuthenticatedTeacherRequestSchema,
        db: Session,
        user_info: CurrentUserReturn,
    ) -> dict[str, str]:
        """Orquesta la creación de una solicitud de nuevo curso para un docente autenticado."""
        repository = AuthenticatedTeacherRequestRepository(db)
        auth = AuthenticatedTeacherRequestController._get_auth_or_raise(
            repository=repository,
            user_info=user_info,
        )
        AuthenticatedTeacherRequestController._validate_no_duplicate_course_request(
            repository=repository,
            auth=auth,
            course_full_name=data.course_full_name,
        )

        teacher_request = repository.create_teacher_request(
            auth_id=auth.id,
            course_full_name=data.course_full_name.strip(),
            groups=data.groups,
        )
        AuthenticatedTeacherRequestController._persist_request_or_raise(
            repository=repository,
            teacher_request=teacher_request,
        )

        return {"message": "Solicitud de curso registrada correctamente."}

    @staticmethod
    def _get_auth_or_raise(
        repository: AuthenticatedTeacherRequestRepository,
        user_info: CurrentUserReturn,
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
        repository: AuthenticatedTeacherRequestRepository,
        auth: Auth,
        course_full_name: str,
    ) -> None:
        """Valida que no exista una solicitud para el mismo curso e instituto."""
        exists_duplicate_request = (
            repository.exists_teacher_request_for_course_and_institute(
                auth_id=auth.id,
                course_full_name=course_full_name,
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

    @staticmethod
    def _persist_request_or_raise(
        repository: AuthenticatedTeacherRequestRepository,
        teacher_request: TeacherCourseRequest,
    ) -> None:
        """Persiste la solicitud y maneja errores de infraestructura de forma genérica."""
        try:
            repository.commit()
            repository.refresh(teacher_request)
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
