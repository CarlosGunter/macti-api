"""
Módulo ListAccountRequestsController - Gestión de Visibilidad de Solicitudes

Este controlador se encarga de filtrar y listar las solicitudes de cuenta
basándose en los privilegios que el usuario tiene dentro de un curso de Moodle.
Implementa un sistema de mapeo de roles (Moodle -> MACTI) y una lógica de
ordenamiento jerárquico por estatus de solicitud.
"""

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
    """
    Controlador para la consulta y filtrado de solicitudes de creación de cuenta.
    Asegura que solo usuarios con roles de gestión (Manager/Teacher) puedan visualizar
    solicitudes de niveles inferiores.
    """

    @staticmethod
    async def list_accounts_requests(
        db: Session,
        course_id: int,
        institute: InstitutesEnum,
        user_info: CurrentUserReturn,
        status: AccountStatusEnum | None = None,
    ):
        """
        Obtiene la lista de solicitudes de cuenta filtradas por curso e instituto.

        Lógica de Negocio:
        1. Consulta los roles del usuario actual directamente en la API de Moodle.
        2. Mapea roles de Moodle a roles internos (ej. MANAGER puede ver DOCENTES).
        3. Aplica filtros de seguridad para que el usuario no vea datos fuera de su alcance.
        4. Ordena los resultados priorizando las solicitudes PENDING.
        """

        # Mapeo de visibilidad: Define qué solicitudes puede ver cada rol de Moodle.
        role_mapping: dict[RoleEnum, AccountRoleEnum] = {
            RoleEnum.MANAGER: AccountRoleEnum.DOCENTE,
            RoleEnum.TEACHER: AccountRoleEnum.ALUMNO,
            RoleEnum.EDITING_TEACHER: AccountRoleEnum.ALUMNO,
        }

        # Validación de identidad externa: Consulta roles en tiempo real en Moodle.
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

        # Determinar qué roles internos puede listar el usuario actual.
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
            # Lógica de ordenamiento: PENDING siempre aparece al principio (prioridad 0).
            status_order = case(
                (UserAccounts.status == AccountStatusEnum.PENDING, 0),
                (UserAccounts.status == AccountStatusEnum.APPROVED, 1),
                (UserAccounts.status == AccountStatusEnum.REJECTED, 2),
                (UserAccounts.status == AccountStatusEnum.CREATED, 3),
                else_=4,
            )

            # Construcción dinámica de filtros de consulta.
            filters = [
                UserAccounts.course_id == course_id,
                UserAccounts.institute == institute,
                UserAccounts.role.in_(internal_roles),
            ]

            if status is not None:
                filters.append(UserAccounts.status == status)

            # Ejecución de la consulta optimizada.
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

            return [dict(r) for r in rows]

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


async def get_user_roles(
    institute: InstitutesEnum,
    course_id: int,
    moodle_id: int,
) -> list[RoleEnum]:
    """
    Función auxiliar que consume el servicio de Moodle para recuperar el perfil
    del usuario y extraer sus roles asignados en un curso específico.
    """

    get_user_profile_result = await MoodleService.get_user_profile(
        institute=institute, user_id=moodle_id, course_id=course_id
    )

    if get_user_profile_result.error:
        return []

    user_roles = get_user_profile_result.user_profile.get("roles", [])
    # Conversión de IDs numéricos de Moodle al Enum RoleEnum para tipado fuerte.
    list_roles = [RoleEnum(role["roleid"]) for role in user_roles]

    return list_roles
