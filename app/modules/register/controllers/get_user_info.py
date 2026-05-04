# Módulo GetUserInfoController - Recuperación de Contexto de Validación
# Este controlador resuelve la identidad de un usuario a partir de un token.
# Permite que el front-end recupere datos de forma segura durante el onboarding.

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.register.repositories.get_user_info_repository import (
    GetUserInfoRepository,
)
from app.modules.register.schemas import CourseRequestInfo, UserInfoResponse


class GetUserInfoController:
    """
    Controlador encargado de validar tokens de verificación y retornar
    la información del usuario asociado.
    """

    @staticmethod
    async def get_user_info(token: str, db: Session) -> UserInfoResponse:
        """
        Recupera los datos básicos del usuario mediante un token.

        Flujo de validación:
        1. Busca el token en la tabla VerificationToken.
        2. Se anexan los datos del usuario asociado al token (ID de auth).
        3. Verifica la expiración.
        4. Retorna la información del usuario si el token es válido.
        """
        repository = GetUserInfoRepository(db)

        token_context = GetUserInfoController._get_token_context_or_raise(
            repository, token
        )
        GetUserInfoController._validate_token_state(token_context)

        return GetUserInfoController._build_response(token_context)

    @staticmethod
    def _get_token_context_or_raise(repository: GetUserInfoRepository, token: str):
        if not token:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "TOKEN_REQUERIDO",
                    "message": "El token de validación es obligatorio.",
                },
            )

        token_context = repository.get_token_context(token)
        if token_context is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "TOKEN_NO_ENCONTRADO",
                    "message": "No se encontró un token de verificación válido.",
                },
            )

        return token_context

    @staticmethod
    def _validate_token_state(token_context) -> None:
        now = datetime.now(token_context.created_at.tzinfo)
        if token_context.is_used:
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "TOKEN_USADO",
                    "message": "El token de verificación ya fue utilizado.",
                },
            )

        if token_context.expires_at < now:
            raise HTTPException(
                status_code=410,
                detail={
                    "error_code": "TOKEN_EXPIRADO",
                    "message": "El token de verificación expiró.",
                },
            )

        if token_context.auth is None or token_context.auth.profile is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "DATOS_INCOMPLETOS",
                    "message": "El token no tiene un perfil de usuario asociado.",
                },
            )

    @staticmethod
    def _build_response(token_context) -> UserInfoResponse:
        auth = token_context.auth
        profile = auth.profile

        # Obtener la solicitud de curso única del usuario
        # Accedemos a las relaciones ya cargadas del token_context
        course_request = GetUserInfoController._get_user_course_request(auth)

        # Se prioriza la información del perfil, porque allí vive el nombre del usuario.
        response_data = {
            "id": auth.id,
            "email": auth.email,
            "name": profile.name,
            "last_name": profile.last_name,
            "role": profile.role,
            "institute": auth.institute,
            "course_request": course_request,
        }

        # Carga secundaria para dejar disponibles las relaciones usadas por el flujo.
        # No se expone en la respuesta, pero evita lazy loading posterior.
        _ = auth.jids

        return UserInfoResponse(**response_data)

    @staticmethod
    def _get_user_course_request(auth) -> CourseRequestInfo:
        """
        Extrae la solicitud de curso del usuario y valida que exista exactamente una.

        Args:
            auth: El objeto Auth del usuario

        Returns:
            CourseRequestInfo con los datos de la solicitud

        Raises:
            HTTPException si no existe solicitud o hay múltiples solicitudes
        """
        student_requests = auth.student_course_requests or []
        teacher_requests = auth.teacher_course_requests or []

        total_requests = len(student_requests) + len(teacher_requests)

        if total_requests == 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "NO_COURSE_REQUEST",
                    "message": "El usuario no tiene una solicitud de curso asociada.",
                },
            )

        if total_requests > 1:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "MULTIPLE_REQUESTS",
                    "message": "El usuario tiene múltiples solicitudes de curso, lo cual viola la lógica del negocio.",
                },
            )

        # Retornar la única solicitud encontrada
        if student_requests:
            request = student_requests[0]
            return CourseRequestInfo(
                id=request.id,
                status=request.status,
                moodle_course_id=request.moodle_course_id,
            )
        else:
            request = teacher_requests[0]
            return CourseRequestInfo(
                id=request.id,
                status=request.status,
                course_full_name=request.course_full_name,
                groups=request.groups,
            )
