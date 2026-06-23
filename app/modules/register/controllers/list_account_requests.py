"""Controlador para listar solicitudes de cuenta visibles para un usuario."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.register.repositories.list_account_requests_repository import (
    ListAccountRequestsRepository,
)
from app.shared.enums.institutes_enum import InstitutesEnum
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

        return ListAccountRequestsController._list_account_requests_or_raise(
            repository=repository,
            course_id=course_id,
            institute=institute,
            status=status,
        )

    @staticmethod
    def _list_account_requests_or_raise(
        repository: ListAccountRequestsRepository,
        course_id: int,
        institute: InstitutesEnum,
        status: RequestStatusEnum | None,
    ) -> list[dict[str, object]]:
        """Delega al repositorio la consulta de solicitudes visibles."""
        try:
            return repository.list_student_account_requests(
                course_id=course_id,
                institute=institute,
                status=status,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "OBTENCION_SOLICITUDES_FALLIDA",
                    "message": "Hubo un error al obtener las solicitudes de cuenta. Intente nuevamente más tarde.",
                },
            ) from exc
