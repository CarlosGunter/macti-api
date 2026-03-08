# Módulo AccountRequestsTeacherController - Gestión de Solicitudes de Docentes
# Este controlador lista las solicitudes de cuenta de docentes. Solo usuarios
# con permisos de administrador definidos en las configuraciones de Moodle
# pueden acceder a esta funcionalidad.

from fastapi import HTTPException
from sqlalchemy import case, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.auth.services.moodle_service import MoodleService
from app.shared.dependecies.get_current_user import CurrentUserReturn
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.users_model import UserAccounts


class AccountRequestsTeacherController:
    """
    Controlador para la consulta de solicitudes de cuenta de docentes.
    Solo usuarios administradores pueden acceder a estas solicitudes.
    """

    @staticmethod
    async def list_teacher_accounts_requests(
        db: Session,
        institute: InstitutesEnum,
        user_info: CurrentUserReturn,
        status: AccountStatusEnum | None = None,
    ):
        """
        Obtiene la lista de solicitudes de cuenta de docentes filtradas por instituto.

        Lógica de Negocio:
        1. Verifica que el usuario sea administrador del instituto.
        2. Filtra solicitudes de docentes por instituto y estado.
        3. Ordena resultados por prioridad de estatus (PENDING primero).
        """

        admin_list = await MoodleService.get_admins(institute=institute)
        if not admin_list:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "CONFIGURACION_INCOMPLETA",
                    "message": f"No se han configurado administradores para el instituto {institute.value}.",
                },
            )

        if user_info.email not in [admin.get("email") for admin in admin_list.admins]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "ACCESO_DENEGADO",
                    "message": "No tienes permisos de administrador para acceder a estas solicitudes.",
                },
            )

        try:
            # Lógica de ordenamiento: PENDING siempre aparece al principio (prioridad 0)
            status_order = case(
                (UserAccounts.status == AccountStatusEnum.PENDING, 0),
                (UserAccounts.status == AccountStatusEnum.APPROVED, 1),
                (UserAccounts.status == AccountStatusEnum.REJECTED, 2),
                (UserAccounts.status == AccountStatusEnum.CREATED, 3),
                else_=4,
            )

            # Construcción dinámica de filtros de consulta
            filters = [
                UserAccounts.institute == institute,
                UserAccounts.role == AccountRoleEnum.DOCENTE,
            ]

            if status is not None:
                filters.append(UserAccounts.status == status)

            # Ejecución de la consulta optimizada
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
