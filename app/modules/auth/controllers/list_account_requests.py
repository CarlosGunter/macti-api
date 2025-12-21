from fastapi import HTTPException
from sqlalchemy import case, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.shared.dependecies.get_current_user import CurrentUserReturn
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_moodle_enum import RoleEnum
from app.shared.services.moodle_service import MoodleService

from ....shared.enums.status_enum import AccountStatusEnum
from ....shared.models.users_model import UserAccounts


class ListAccountRequestsController:
    @staticmethod
    async def list_accounts_requests(
        db: Session,
        course_id: int,
        institute: InstitutesEnum,
        user_info: CurrentUserReturn,
        status: AccountStatusEnum | None = None,
    ):
        # Verificar si el usuario tiene el rol de profesor en el curso
        has_role = await verify_capability(
            institute=institute,
            course_id=course_id,
            moodle_id=user_info.moodle_id,
            capability_name=RoleEnum.TEACHER,
        )

        if not has_role:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "SIN_PERMISOS",
                    "message": "Sin privilegios para ver las solicitudes de este curso.",
                },
            )

        try:
            # Hacer una selección explícita y usar mappings() para obtener dicts
            status_order = case(
                (UserAccounts.status == AccountStatusEnum.PENDING, 0),
                (UserAccounts.status == AccountStatusEnum.APPROVED, 1),
                (UserAccounts.status == AccountStatusEnum.REJECTED, 2),
                (UserAccounts.status == AccountStatusEnum.CREATED, 3),
                else_=4,
            )

            filters = [
                UserAccounts.course_id == course_id,
                UserAccounts.institute == institute,
            ]

            if status is not None:
                filters.append(UserAccounts.status == status)

            stmt = (
                select(
                    UserAccounts.id,
                    UserAccounts.name,
                    UserAccounts.last_name,
                    UserAccounts.email,
                    UserAccounts.status,
                )
                .where(*filters)
                .order_by(status_order, UserAccounts.status)
            )

            result = db.execute(stmt)
            rows = result.mappings().all()

            # Para que coincida exactamente con el response_model
            return [dict(r) for r in rows]

        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error al obtener solicitudes",
                },
            ) from exc

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error_code": "ERROR_DESCONOCIDO", "message": str(e)},
            ) from e


async def verify_capability(
    institute: InstitutesEnum,
    course_id: int,
    moodle_id: int,
    capability_name: str,
) -> bool:
    """
    Dependencia que verifica si un usuario tiene un rol específico en un curso dado.
    """

    get_user_profile_result = await MoodleService.get_user_profile(
        institute=institute, user_id=moodle_id, course_id=course_id
    )

    if get_user_profile_result.error:
        return False

    user_roles = get_user_profile_result.user_profile.get("roles", [])
    has_role = any(
        int(role.get("roleid", 0)) == int(capability_name) for role in user_roles
    )

    return has_role
