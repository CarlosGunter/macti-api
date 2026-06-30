from typing import Annotated

from fastapi import Depends, HTTPException, Query

from app.shared.dependecies.auth_current_user import CurrentUser, get_current_user
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.services.moodle_service import MoodleService


class AuthScopes:
    """
    Clase base para verificar roles de usuario en dependencias de FastAPI.
    """

    def __init__(self, required_role: AccountRoleEnum):
        self.required_role = required_role
        self.required_level = required_role.level

    async def __call__(
        self,
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
        institute: InstitutesEnum = Query(..., description="Instituto"),
    ) -> bool | None:
        """
        Verifica si el usuario autenticado tiene el rol requerido.

        Args:
            institute (InstitutesEnum): Instituto al que pertenece el usuario.
            current_user (CurrentUser): Usuario autenticado obtenido de la dependencia `get_current_user`.

        Raises:
            HTTPException: Si el usuario no tiene el rol requerido.
        """

        moodle_admin_list = await MoodleService.get_admins(institute)
        admin_list = moodle_admin_list.admins if moodle_admin_list.success else []

        is_admin = any(admin["email"] == current_user.email for admin in admin_list)

        if not is_admin and self.required_role == AccountRoleEnum.ADMIN:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "SIN_PERMISOS",
                    "message": "El usuario no tiene permisos para realizar esta acción.",
                },
            )

        return is_admin
