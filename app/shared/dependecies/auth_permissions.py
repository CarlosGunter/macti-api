from fastapi import Depends, HTTPException, status

from app.shared.dependecies.auth_current_user import CurrentUser, get_current_user
from app.shared.enums.role_enum import AccountRoleEnum


class BasePermissionChecker:
    def __init__(self, required_role: AccountRoleEnum):
        # Ahora el constructor recibe una instancia del Enum de manera estricta
        self.required_role = required_role
        self.required_level = required_role.level

    def __call__(
        self, authenticated_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        # Validación piramidal pura utilizando las propiedades del Enum
        if authenticated_user.role.level < self.required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "mensaje": f"Acceso denegado. Se requiere al menos nivel de {self.required_role.value}.",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                },
            )

        return authenticated_user
