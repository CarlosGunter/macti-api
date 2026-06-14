"""Controlador para listar solicitudes de cuenta de docentes."""

from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.register.repositories.list_account_requests_teacher_repository import (
    ListTeacherAccountRequestsRepository,
)
from app.modules.register.services.moodle_service import MoodleService
from app.shared.dependecies.auth_current_user import CurrentUser
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.status_enum import RequestStatusEnum


class AccountRequestsTeacherController:
    """Controlador para la consulta de solicitudes de cuenta de docentes."""

    @staticmethod
    async def list_teacher_accounts_requests(
        db: Session,
        institute: InstitutesEnum,
        user_info: CurrentUser,
        status: RequestStatusEnum | None = None,
    ) -> list[dict[str, object]]:
        """Obtiene la lista de solicitudes de docentes visibles para un administrador."""

        repository = ListTeacherAccountRequestsRepository(db)

        admins = await AccountRequestsTeacherController._get_admins_or_raise(
            institute=institute
        )
        AccountRequestsTeacherController._validate_admin_access(
            user_info=user_info,
            admins=admins,
        )
        rows = AccountRequestsTeacherController._get_teacher_requests_or_raise(
            repository=repository,
            institute=institute,
            status=status,
        )
        return AccountRequestsTeacherController._build_response(rows)

    @staticmethod
    async def _get_admins_or_raise(
        institute: InstitutesEnum,
    ) -> Any:
        """Recupera los administradores del instituto o retorna un error HTTP."""
        admin_list = await MoodleService.get_admins(institute=institute)
        if not admin_list:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "CONFIGURACION_INCOMPLETA",
                    "message": f"No se han configurado administradores para el instituto {institute.value}.",
                },
            )

        return admin_list.admins

    @staticmethod
    def _validate_admin_access(
        user_info: CurrentUser,
        admins: Sequence[dict[str, Any]],
    ) -> None:
        """Valida que el usuario autenticado pertenezca a la lista de administradores."""
        admin_emails = [admin.get("email") for admin in admins]
        if user_info.email not in admin_emails:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "ACCESO_DENEGADO",
                    "message": "No tienes permisos de administrador para acceder a estas solicitudes.",
                },
            )

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
