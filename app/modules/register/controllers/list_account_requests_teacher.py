"""Controlador para listar solicitudes de cuenta de docentes."""

from typing import Any

from sqlalchemy.orm import Session

from app.modules.register.repositories.list_account_requests_teacher_repository import (
    ListTeacherAccountRequestsRepository,
)
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.status_enum import RequestStatusEnum


class AccountRequestsTeacherController:
    """Controlador para la consulta de solicitudes de cuenta de docentes."""

    @staticmethod
    async def list_teacher_accounts_requests(
        db: Session,
        institute: InstitutesEnum,
        status: RequestStatusEnum | None = None,
    ) -> list[dict[str, object]]:
        """Obtiene la lista de solicitudes de docentes visibles para un administrador."""

        repository = ListTeacherAccountRequestsRepository(db)

        rows = AccountRequestsTeacherController._get_teacher_requests_or_raise(
            repository=repository,
            institute=institute,
            status=status,
        )
        return AccountRequestsTeacherController._build_response(rows)

    @staticmethod
    def _get_teacher_requests_or_raise(
        repository: ListTeacherAccountRequestsRepository,
        institute: InstitutesEnum,
        status: RequestStatusEnum | None,
    ) -> list[dict[str, Any]]:
        """Obtiene las solicitudes docentes desde el repositorio."""
        return repository.list_teacher_account_requests(
            institute=institute,
            status=status,
        )

    @staticmethod
    def _build_response(rows: list[dict[str, Any]]) -> list[dict[str, object]]:
        """Convierte los registros crudos en la estructura pública de respuesta."""
        return [
            {
                "user": AccountRequestsTeacherController._build_user_payload(row),
                "courses": AccountRequestsTeacherController._build_course_payload(row),
            }
            for row in rows
        ]

    @staticmethod
    def _build_user_payload(row: dict[str, Any]) -> dict[str, object]:
        """Construye el bloque user de la respuesta."""
        return {
            "id": row["user_id"],
            "name": row["name"],
            "last_name": row["last_name"],
            "email": row["email"],
            "role": row["role"],
            "institute": row["institute"],
        }

    @staticmethod
    def _build_course_payload(row: dict[str, Any]) -> dict[str, object]:
        """Construye el bloque courses de la respuesta."""
        return {
            "id": row["course_request_id"],
            "status": row["status"],
            "course_full_name": row["course_full_name"],
            "groups": AccountRequestsTeacherController._split_groups(row["groups"]),
        }

    @staticmethod
    def _split_groups(groups: str | None) -> list[str]:
        """Convierte los grupos almacenados como CSV en una lista limpia."""
        return [group.strip() for group in (groups or "").split(",") if group.strip()]
