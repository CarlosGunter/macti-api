"""Repositorio para la consulta de solicitudes de cuenta de docentes."""

from typing import Any

from sqlalchemy import case, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Select

from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import RequestStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.user_profiles_model import UserProfile


class ListTeacherAccountRequestsRepository:
    """Encapsula la lectura de solicitudes de cuenta de docentes."""

    def __init__(self, db: Session) -> None:
        """Inicializa el repositorio con la sesión activa de base de datos."""
        self.db = db

    def list_teacher_account_requests(
        self,
        institute: InstitutesEnum,
        status: RequestStatusEnum | None = None,
    ) -> list[dict[str, Any]]:
        """Retorna las solicitudes de docentes con los campos requeridos por el controlador."""
        stmt = self._build_statement(institute=institute, status=status)
        rows = self.db.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def _build_statement(
        self,
        institute: InstitutesEnum,
        status: RequestStatusEnum | None,
    ) -> Select[
        tuple[
            int,
            str,
            str,
            str,
            AccountRoleEnum,
            InstitutesEnum,
            int,
            RequestStatusEnum,
            str,
            str,
        ]
    ]:
        """Construye la consulta para listar solicitudes de docentes."""
        status_order = self._build_status_order()
        filters = self._build_filters(institute=institute, status=status)

        return (
            select(
                Auth.id.label("user_id"),
                UserProfile.name.label("name"),
                UserProfile.last_name.label("last_name"),
                Auth.email.label("email"),
                UserProfile.role.label("role"),
                Auth.institute.label("institute"),
                TeacherCourseRequest.id.label("course_request_id"),
                TeacherCourseRequest.status.label("status"),
                TeacherCourseRequest.course_full_name.label("course_full_name"),
                TeacherCourseRequest.groups.label("groups"),
            )
            .join(Auth, TeacherCourseRequest.auth_id == Auth.id)
            .join(UserProfile, UserProfile.auth_id == Auth.id)
            .where(*filters)
            .order_by(status_order, TeacherCourseRequest.status)
        )

    @staticmethod
    def _build_status_order() -> ColumnElement[int]:
        """Define el orden de prioridad para el estatus de las solicitudes."""
        return case(
            (TeacherCourseRequest.status == RequestStatusEnum.PENDING, 0),
            (TeacherCourseRequest.status == RequestStatusEnum.APPROVED, 1),
            (TeacherCourseRequest.status == RequestStatusEnum.REJECTED, 2),
            (TeacherCourseRequest.status == RequestStatusEnum.ENROLLED, 3),
            else_=4,
        )

    @staticmethod
    def _build_filters(
        institute: InstitutesEnum,
        status: RequestStatusEnum | None,
    ) -> list[ColumnElement[bool]]:
        """Construye los filtros base de la consulta."""
        filters: list[ColumnElement[bool]] = [
            Auth.institute == institute,
        ]

        if status is not None:
            filters.append(TeacherCourseRequest.status == status)

        return filters
