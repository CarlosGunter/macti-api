# Módulo CreateAccountController - Aprovisionamiento de Servicios Externos
# Coordina la creación de usuarios en Keycloak y Moodle, además de la
# inscripción a cursos, creación de grupos y limpieza de tokens de verificación.

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.register.repositories.create_account_repository import (
    CreateAccountRepository,
)
from app.modules.register.services.kc_service import KeycloakService
from app.modules.register.services.moodle_service import MoodleService
from app.modules.register.use_cases.enroll_user import EnrollUserUseCase
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest

from ..schemas import CreateAccountSchema


class CreateAccountController:
    """Controlador que orquesta el aprovisionamiento final de una cuenta.

    Separa responsabilidades en funciones privadas para claridad y testabilidad.
    """

    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session) -> dict[str, Any]:
        """Flujo principal de creación de cuenta.

        Args:
            data: `CreateAccountSchema` con `user_id`, `new_password` y `token`.
            db: Sesión de SQLAlchemy.

        Returns:
            Diccionario con IDs creados y mensaje de éxito.
        """
        repo = CreateAccountRepository(db)

        auth = repo.get_auth_with_relations(data.user_id)
        if auth is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "USUARIO_NO_ENCONTRADO",
                    "message": "No se encontró una solicitud de cuenta con el ID proporcionado",
                },
            )

        CreateAccountController._validate_verification_tokens(auth, data.token)
        CreateAccountController._validate_request_approved(auth)

        # KEYCLOAK
        kc_user_id = await CreateAccountController._recover_existing_kc(auth)
        if not kc_user_id:
            kc_user_id = await CreateAccountController._create_user_kc_or_raise(
                auth, data.new_password
            )

        # MOODLE - crear usuario y delegar la resolución de cursos al caso de uso
        moodle_user_id = await CreateAccountController._create_moodle_user_or_raise(
            auth
        )
        approved_request = CreateAccountController._get_approved_course_request(auth)
        enroll_user_use_case = EnrollUserUseCase(
            moodle_service=MoodleService(), institute=auth.institute
        )
        enroll_result = await enroll_user_use_case.execute(
            request_course_data=approved_request,
            user_id=moodle_user_id,
        )
        if not enroll_result.enrolled:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "INSCRIPCION_ERROR",
                    "message": f"Error al inscribir al usuario en el curso: {enroll_result.error}",
                },
            )

        # Finalizar: actualizar estados y limpiar token
        CreateAccountController._finalize_transaction(
            repo=repo, auth=auth, kc_user_id=kc_user_id, moodle_user_id=moodle_user_id
        )

        return {"message": "Cuenta creada exitosamente"}

    @staticmethod
    def _validate_verification_tokens(auth: Auth, token: UUID) -> None:
        """Valida el token único de verificación asociado al `Auth`.

        Requisitos:
        - Existe exactamente un `verification_token` asociado (relación 1:1).
        - El `token` proporcionado (UUID) coincide con `verification_token.token`.
        - `verification_token.is_used` es `False`.
        - `verification_token.expires_at` es posterior al instante actual (UTC).

        Errores lanzados (HTTP 400):
        - `TOKEN_NO_ENCONTRADO` si no existe token asociado.
        - `TOKEN_INVALIDO` si el token no coincide, está usado o expirado.
        """

        if auth.verification_token is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "TOKEN_NO_ENCONTRADO",
                    "message": "No se encontró un token de verificación asociado a esta solicitud",
                },
            )

        if auth.verification_token.token != token:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "TOKEN_INVALIDO",
                    "message": "El token de verificación proporcionado no es válido para esta solicitud",
                },
            )

        if auth.verification_token.is_used:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "TOKEN_INVALIDO",
                    "message": "El token de verificación ya ha sido utilizado",
                },
            )

        if auth.verification_token.expires_at < datetime.now(
            tz=auth.verification_token.expires_at.tzinfo
        ):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "TOKEN_INVALIDO",
                    "message": "El token de verificación ha expirado",
                },
            )

    @staticmethod
    def _validate_request_approved(auth: Auth) -> None:
        """Valida que exista una solicitud de curso aprobada para este usuario.

        Según el flujo:
        - El usuario solo puede tener una solicitud pendiente.
        - El modelo permite múltiples solicitudes futuras.
        - Se valida que en este punto solo exista una solicitud aprobada.
        """
        all_requests = auth.student_course_requests + auth.teacher_course_requests

        if len(all_requests) != 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "ESTADO_SOLICITUD_INVALIDO",
                    "message": "Se requiere exactamente una solicitud de curso para esta cuenta",
                },
            )

        if all_requests[0].status != RequestStatusEnum.APPROVED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "ESTADO_SOLICITUD_INVALIDO",
                    "message": "La solicitud de curso no está aprobada para esta cuenta",
                },
            )

    @staticmethod
    async def _create_user_kc_or_raise(auth: Auth, password: str) -> UUID:
        """Crea el usuario en Keycloak o recupera su ID si ya existe.

        Divide la lógica para reducir complejidad cognitiva.
        """
        profile = auth.profile

        kc_result = await KeycloakService.create_user(
            {
                "name": profile.name,
                "last_name": profile.last_name,
                "email": auth.email,
                "password": password,
            },
            institute=auth.institute,
        )

        if not kc_result.user_id:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "KC_ERROR",
                    "message": f"Error en Keycloak: {kc_result.error}",
                },
            )

        return kc_result.user_id

    @staticmethod
    async def _recover_existing_kc(auth: Auth) -> UUID | None:
        """Recupera un usuario existente en Keycloak por correo y guarda su ID.

        Busca el usuario por email en Keycloak y almacena su `kc_id` en el
        registro `JIDs` asociado al `auth`. Lanza `HTTPException` si no se
        puede recuperar el ID.
        """
        existing_user = await KeycloakService.get_user_by_email(
            email=auth.email, institute=auth.institute
        )

        return (
            UUID(existing_user.user.get("id"))
            if existing_user.found and existing_user.user
            else None
        )

    @staticmethod
    def _get_approved_course_request(
        auth: Auth,
    ) -> StudentCourseRequest | TeacherCourseRequest:
        """Recupera la solicitud de curso aprobada que define el contexto de matrícula."""
        if auth.profile.role == AccountRoleEnum.ALUMNO:
            return auth.student_course_requests[0]
        else:
            return auth.teacher_course_requests[0]

    @staticmethod
    async def _create_moodle_user_or_raise(auth: Auth) -> int:
        """Crea el usuario en Moodle; lanza y permite rollback si falla.

        Crea el usuario en la instancia de Moodle y almacena el `moodle_id`
        en el registro `JIDs` del `auth`. Si no existe `JIDs`, lo crea.
        """
        profile = auth.profile

        moodle_result = await MoodleService.create_user(
            user_data={
                "name": profile.name,
                "last_name": profile.last_name,
                "email": auth.email,
            },
            institute=auth.institute,
        )

        if not moodle_result.user_id:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": "Error al crear usuario en Moodle",
                },
            )

        return moodle_result.user_id

    @staticmethod
    def _finalize_transaction(
        repo: CreateAccountRepository, auth: Auth, kc_user_id: UUID, moodle_user_id: int
    ) -> None:
        """Actualiza estados locales, elimina tokens y persiste la transacción."""

        # Guardar IDs de servicios externos en JIDs
        jid_entry = repo.save_jids(
            auth_id=auth.id,
            kc_id=kc_user_id,
            moodle_id=moodle_user_id,
        )

        repo.activate_auth_account(auth.id)

        # Eliminar token
        repo.delete_verification_token(auth.id)

        # Persistir
        repo.commit()
        repo.refresh(jid_entry)
