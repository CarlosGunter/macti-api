from typing import Annotated

from fastapi import Depends, HTTPException, Query

from app.shared.dependecies.auth_current_user import CurrentUser, get_current_user
from app.shared.dependecies.auth_scopes_base import AuthScopes
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.role_moodle_enum import RoleEnum
from app.shared.services.moodle_service import MoodleService


class ScopeCourseManager(AuthScopes):
    """
    Clase de dependencia para verificar si el usuario autenticado tiene el rol de profesor
    en un curso específico.
    """

    def __init__(self):
        super().__init__(AccountRoleEnum.DOCENTE)

    async def __call__(
        self,
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
        institute: InstitutesEnum = Query(..., description="Instituto"),
        course_id: int = Query(..., description="ID del curso en Moodle"),
    ):
        """
        Verifica si el usuario autenticado tiene el rol de profesor en un curso específico.

        Args:
            course_id (int): ID del curso a verificar.
            current_user (CurrentUser): Usuario autenticado obtenido de la dependencia `get_current_user`.

        Raises:
            HTTPException: Si el usuario no tiene el rol de profesor en el curso especificado.
        """
        is_admin = await super().__call__(
            institute=institute, current_user=current_user
        )
        if is_admin:
            return  # El usuario es administrador, no se necesita más verificación

        user_roles = await self._get_user_roles_or_raise(
            course_id=course_id,
            institute=institute,
            user_info=current_user,
        )

        self._get_internal_roles_or_raise(user_roles=user_roles)

    async def _get_user_roles_or_raise(
        self,
        course_id: int,
        institute: InstitutesEnum,
        user_info: CurrentUser,
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
                    "error_code": "SIN_ROLES",
                    "message": "No tiene roles asignados en Moodle para este curso",
                },
            )

        return user_roles

    def _get_internal_roles_or_raise(
        self,
        user_roles: list[RoleEnum],
    ):
        """
        Verifica si el usuario tiene al menos uno de los roles internos permitidos para gestionar el curso.
        """
        role_access = [
            RoleEnum.MANAGER,
            RoleEnum.TEACHER,
            RoleEnum.EDITING_TEACHER,
        ]

        is_authorized = any(role in role_access for role in user_roles)

        if not is_authorized:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "SIN_PERMISOS",
                    "message": "No tienes permisos para gestionar este curso.",
                },
            )
