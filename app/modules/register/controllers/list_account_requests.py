"""Controlador para listar solicitudes de cuenta visibles para un usuario."""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.register.repositories.list_account_requests_repository import (
    ListAccountRequestsRepository,
)
from app.modules.register.services.moodle_service import MoodleService
from app.shared.dependecies.get_current_user import CurrentUserReturn
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.role_moodle_enum import RoleEnum
from app.shared.enums.status_enum import RequestStatusEnum


class ListAccountRequestsController:
    """
    Controlador encargado de orquestar la consulta de solicitudes de cuenta
    visibles para el usuario actual.
    """

    @staticmethod
    async def list_accounts_requests(
        db: Session,
        course_id: int,
        institute: InstitutesEnum,
        user_info: CurrentUserReturn,
        status: RequestStatusEnum | None = None,
    ) -> list[dict[str, object]]:
        """
        Obtiene solicitudes de cuenta filtradas por curso, instituto y estado.

        Args:
            db: Sesión de base de datos.
            course_id: Identificador del curso en Moodle.
            institute: Instituto al que pertenece la solicitud.
            user_info: Datos del usuario autenticado.
            status: Filtro opcional por estatus.

        Returns:
            Lista de solicitudes visibles para el usuario.
        """
        repository = ListAccountRequestsRepository(db)

        try:
            user_roles = await ListAccountRequestsController._get_user_roles_or_raise(
                course_id=course_id,
                institute=institute,
                user_info=user_info,
            )
            internal_roles = ListAccountRequestsController._get_internal_roles_or_raise(
                user_roles=user_roles,
            )

            return ListAccountRequestsController._list_account_requests_or_raise(
                repository=repository,
                course_id=course_id,
                institute=institute,
                internal_roles=internal_roles,
                status=status,
            )
        except HTTPException:
            raise

        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error al obtener solicitudes de la base de datos",
                },
            ) from exc

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error_code": "ERROR_DESCONOCIDO", "message": str(e)},
            ) from e

    @staticmethod
    async def _get_user_roles_or_raise(
        course_id: int,
        institute: InstitutesEnum,
        user_info: CurrentUserReturn,
    ) -> list[RoleEnum]:
        """Recupera los roles Moodle del usuario y valida que existan."""
        user_roles = await MoodleService.get_user_roles(
            institute=institute,
            course_id=course_id,
            moodle_id=user_info.moodle_id,
        )

        if not user_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "SIN_PERMISOS",
                    "message": "Sin privilegios para ver las solicitudes de este curso.",
                },
            )

        return user_roles

    @staticmethod
    def _get_internal_roles_or_raise(
        user_roles: list[RoleEnum],
    ) -> list[AccountRoleEnum]:
        """Convierte los roles de Moodle a los roles internos visibles."""
        role_mapping: dict[RoleEnum, AccountRoleEnum] = {
            RoleEnum.MANAGER: AccountRoleEnum.ALUMNO,
            RoleEnum.TEACHER: AccountRoleEnum.ALUMNO,
            RoleEnum.EDITING_TEACHER: AccountRoleEnum.ALUMNO,
        }

        internal_roles = [
            role_mapping[role] for role in user_roles if role in role_mapping
        ]

        if not internal_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "SIN_PERMISOS",
                    "message": "No tiene roles válidos para ver solicitudes en este curso.",
                },
            )

        return internal_roles

    @staticmethod
    def _list_account_requests_or_raise(
        repository: ListAccountRequestsRepository,
        course_id: int,
        institute: InstitutesEnum,
        internal_roles: list[AccountRoleEnum],
        status: RequestStatusEnum | None,
    ) -> list[dict[str, object]]:
        """Delega al repositorio la consulta de solicitudes visibles."""
        return repository.list_student_account_requests(
            course_id=course_id,
            institute=institute,
            internal_roles=internal_roles,
            status=status,
        )
