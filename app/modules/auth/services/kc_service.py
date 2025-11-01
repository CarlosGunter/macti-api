import httpx

from app.core.config import settings


class KeycloakService:
    BASE_URL = settings.KEYCLOAK_SERVER_URL
    REALM = settings.KEYCLOAK_REALM
    TOKEN_URL = f"{BASE_URL}/realms/{REALM}/protocol/openid-connect/token"
    USERS_API_URL = f"{BASE_URL}/admin/realms/{REALM}/users"

    @classmethod
    async def _get_admin_token(cls) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    cls.TOKEN_URL,
                    data={
                        "client_id": settings.KEYCLOAK_ADMIN_CLIENT_ID,
                        "client_secret": settings.KEYCLOAK_ADMIN_CLIENT_SECRET,
                        "grant_type": "client_credentials",
                    },
                )
                response.raise_for_status()
                return response.json()["access_token"]
        except Exception as e:
            error_message = f"Fallo al autenticar con Keycloak Admin API: {e}"
            print(error_message)
            raise Exception(error_message)

    @classmethod
    async def create_user(cls, user_data: dict) -> dict:
        try:
            token = await cls._get_admin_token()
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
                    cls.USERS_API_URL,
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code in [201, 204]:
                    created_user = await cls.get_user_by_email(user_data["email"])
                    return {"created": True, "user_id": created_user.get("id")}
                else:
                    return {"created": False, "error": response.text}
        except Exception as e:
            return {"created": False, "error": str(e)}

    @classmethod
    async def get_user_by_email(cls, email: str) -> dict:
        token = await cls._get_admin_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                cls.USERS_API_URL,
                params={"email": email},
                headers={"Authorization": f"Bearer {token}"},
            )
            users = response.json()
            return users[0] if users else {}

    @classmethod
    async def delete_user(cls, user_id: str) -> bool:
        try:
            token = await cls._get_admin_token()
            async with httpx.AsyncClient() as client:
                url = f"{cls.USERS_API_URL}/{user_id}"
                response = await client.delete(
                    url, headers={"Authorization": f"Bearer {token}"}
                )
                return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error deleting Keycloak user {user_id}: {e}")
            return False

    # Actualiza la contraseña de un usuario en Keycloak
    @classmethod
    async def update_user_password(cls, user_id: str, new_password: str) -> dict:
        try:
            token = await cls._get_admin_token()
            payload = {"type": "password", "value": new_password, "temporary": False}
            async with httpx.AsyncClient() as client:
                url = f"{cls.USERS_API_URL}/{user_id}/reset-password"
                response = await client.put(
                    url, json=payload, headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 204:
                    return {"success": True}
                else:
                    return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
