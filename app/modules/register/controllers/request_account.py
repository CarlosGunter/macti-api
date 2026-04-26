# Módulo RequestAccountController - Captura y Validación de Solicitudes
#
# Este controlador es la puerta de entrada para los nuevos usuarios en el sistema.
# Maneja la lógica inicial de registro para Alumnos y Docentes, validando duplicados
# y generando códigos de identificación interna (Subjects) para personal académico.


from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.register.repositories.request_account_repository import (
    RequestAccountRepository,
)
from app.modules.register.services.kc_service import KeycloakService
from app.shared.enums.role_enum import AccountRoleEnum

from ..schemas import StudentRequestSchema, TeacherRequestSchema


class RequestAccountController:
    """
    Controlador encargado de procesar las peticiones iniciales de registro de cuenta.
    Incluye lógica de validación de correo único por instituto y generación de logs.
    """

    @staticmethod
    async def request_account(
        role: AccountRoleEnum,
        data: StudentRequestSchema | TeacherRequestSchema,
        db: Session,
    ):
        """
        Punto de entrada principal para registrar una solicitud de cuenta.

        Args:
            role: ALUMNO o DOCENTE
            data: Datos de la solicitud (varía según el rol)
            db: Sesión de base de datos

        Returns:
            dict: Mensaje de éxito
        """
        repository = RequestAccountRepository(db)

        try:
            RequestAccountController._validate_no_duplicate_request(repository, data)
            await RequestAccountController._validate_no_existing_keycloak_user(data)
            RequestAccountController._create_request(repository, role, data)
            return {"message": "Solicitud de cuenta registrada correctamente."}
        except HTTPException:
            repository.rollback()
            raise  # La excepción ya está manejada
        except SQLAlchemyError as exc:
            repository.rollback()
            print(f"Error de base de datos: {exc}")  # Log detallado para debugging
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Ocurrió un error al guardar la solicitud de cuenta.",
                },
            ) from exc
        except Exception as exc:
            repository.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ERROR_INTERNO",
                    "message": "Ocurrió un error inesperado al procesar la solicitud.",
                },
            ) from exc

    @staticmethod
    def _validate_no_duplicate_request(
        repository: RequestAccountRepository,
        data: StudentRequestSchema | TeacherRequestSchema,
    ) -> None:
        existing_request = repository.get_by_email_and_institute(
            data.email, data.institute
        )

        if existing_request is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "DUPLICADO",
                    "message": "Ya existe una solicitud para este correo e instituto",
                },
            )

    @staticmethod
    async def _validate_no_existing_keycloak_user(
        data: StudentRequestSchema | TeacherRequestSchema,
    ) -> None:
        if await KeycloakService.user_exists(data.email, data.institute):
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EXISTE_KEYCLOAK",
                    "message": "Ya tienes una cuenta activa. Inicia sesión para solicitar acceso a cursos.",
                },
            )

    @staticmethod
    def _create_request(
        repository: RequestAccountRepository,
        role: AccountRoleEnum,
        data: StudentRequestSchema | TeacherRequestSchema,
    ) -> None:
        db_request = repository.create_account_request(role=role, data=data)
        repository.commit()
        repository.refresh(db_request)
