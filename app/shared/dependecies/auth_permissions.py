from fastapi import Depends, HTTPException, status

from app.shared.dependecies.auth_verify import validate_jwt_token


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(validate_jwt_token)):
        user_role = current_user.get("role")

        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los permisos necesarios para realizar esta acción",
            )

        return current_user
