from fastapi import HTTPException
from sqlalchemy import case, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.shared.dependecies.get_current_user import CurrentUserReturn
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
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
        # Diccionario para mapear los roles de Moodle a los roles internos
        role_mapping: dict[RoleEnum, AccountRoleEnum] = {
            RoleEnum.MANAGER: AccountRoleEnum.DOCENTE,
            RoleEnum.TEACHER: AccountRoleEnum.ALUMNO,
            RoleEnum.EDITING_TEACHER: AccountRoleEnum.ALUMNO,
        }

        # Obtener los roles del usuario en el curso
        user_roles = await get_user_roles(
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

        # Mapear los roles de Moodle del usuario a roles internos
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
                UserAccounts.role.in_(internal_roles),
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
                    UserAccounts.role,
                )
                .where(*filters)
                .order_by(status_order, UserAccounts.status)
            )

            result = db.execute(stmt)
            rows = result.mappings().all()

            # Agrupar las solicitudes por rol
            grouped_by_role: dict[str, list[dict]] = {}
            for row in rows:
                row_dict = dict(row)
                role = row_dict.pop("role")  # Extraer el rol y removerlo del dict
                role_key = role.value if role else "SIN_ROL"

                if role_key not in grouped_by_role:
                    grouped_by_role[role_key] = []

                grouped_by_role[role_key].append(row_dict)

            return grouped_by_role

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


async def get_user_roles(
    institute: InstitutesEnum,
    course_id: int,
    moodle_id: int,
) -> list[RoleEnum]:
    """
    Dependencia que obtiene los roles de un usuario en un curso dado.
    """

    get_user_profile_result = await MoodleService.get_user_profile(
        institute=institute, user_id=moodle_id, course_id=course_id
    )

    if get_user_profile_result.error:
        return []

    user_roles = get_user_profile_result.user_profile.get("roles", [])
    list_roles = [RoleEnum(role["roleid"]) for role in user_roles]

    return list_roles
