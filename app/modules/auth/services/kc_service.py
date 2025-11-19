# app/modules/auth/services/kc_service.py
import httpx

from app.shared.config.kc_configs import keycloak_configs


class KeycloakService:
    """Servicio para interactuar con Keycloak en distintos institutos."""

    @classmethod
    async def _get_admin_token(cls, institute: str) -> str:
        """Obtiene el token de administrador de un instituto específico."""
        try:
            config = keycloak_configs[institute.lower()]
            token_url = f"{config['url']}/realms/{config['realm']}/protocol/openid-connect/token"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data={
                        "client_id": config["clientId"],
                        "client_secret": config["secretPass"],
                        "grant_type": "client_credentials",
                    },
                )
                response.raise_for_status()
                return response.json()["access_token"]
        except Exception as e:
            error_message = f"Fallo al autenticar con Keycloak ({institute}): {e}"
            print(error_message)
            raise Exception(error_message) from e

    @classmethod
    async def create_user(cls, user_data: dict, institute: str) -> dict:
        """Crea un usuario en el Keycloak del instituto especificado."""
        print(f" KeycloakService.create_user called for institute={institute}")
        try:
            config = keycloak_configs[institute.lower()]
            token = await cls._get_admin_token(institute)
            users_api_url = f"{config['url']}/admin/realms/{config['realm']}/users"

            payload = {
                "username": user_data["email"],
                "email": user_data["email"],
                "firstName": user_data["name"],
                "lastName": user_data["last_name"],
                "enabled": True,
                "credentials": [
                    {
                        "type": "password",
                        "value": user_data["password"],
                        "temporary": False,
                    }
                ],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    users_api_url,
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code in [201, 204]:
                    created_user = await cls.get_user_by_email(
                        user_data["email"], institute
                    )
                    return {"created": True, "user_id": created_user.get("id")}
                else:
                    return {"created": False, "error": response.text}
        except Exception as e:
            return {"created": False, "error": str(e)}

    @classmethod
    async def get_user_by_email(cls, email: str, institute: str) -> dict:
        """Busca un usuario por correo electrónico."""
        config = keycloak_configs[institute.lower()]
        token = await cls._get_admin_token(institute)
        users_api_url = f"{config['url']}/admin/realms/{config['realm']}/users"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                users_api_url,
                params={"email": email},
                headers={"Authorization": f"Bearer {token}"},
            )
            users = response.json()
            return users[0] if users else {}

    @classmethod
    async def delete_user(cls, user_id: str, institute: str) -> bool:
        """Elimina un usuario en Keycloak."""
        try:
            config = keycloak_configs[institute.lower()]
            token = await cls._get_admin_token(institute)
            users_api_url = f"{config['url']}/admin/realms/{config['realm']}/users"

            async with httpx.AsyncClient() as client:
                url = f"{users_api_url}/{user_id}"
                response = await client.delete(
                    url, headers={"Authorization": f"Bearer {token}"}
                )
                return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error deleting Keycloak user {user_id}: {e}")
            return False

    @classmethod
    async def update_user_password(
        cls, user_id: str, new_password: str, institute
    ) -> dict:
        """Actualiza la contraseña de un usuario en Keycloak."""
        try:
            # Normalizar valor de institute (puede ser Enum, str o None)
            if institute is None:
                institute_key = "principal"
            elif hasattr(institute, "value"):
                institute_key = institute.value.lower()
            elif isinstance(institute, str):
                institute_key = institute.lower()
            else:
                raise ValueError(f"Tipo de instituto no válido: {type(institute)}")

            config = keycloak_configs[institute_key]
            token = await cls._get_admin_token(institute_key)

            url = f"{config['url']}/admin/realms/{config['realm']}/users/{user_id}/reset-password"
            payload = {"type": "password", "value": new_password, "temporary": False}

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url, json=payload, headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 204:
                    return {"success": True}
                else:
                    return {"success": False, "error": response.text}

        except Exception as e:
            return {"success": False, "error": str(e)}
