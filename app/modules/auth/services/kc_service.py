import httpx
from app.core.config import settings
from typing import Dict, Any

class KeycloakService:
    BASE_URL = settings.KEYCLOAK_SERVER_URL 
    REALM = settings.KEYCLOAK_REALM
    
    TOKEN_URL = f"{BASE_URL}/realms/{REALM}/protocol/openid-connect/token"
    USERS_API_URL = f"{BASE_URL}/admin/realms/{REALM}/users"

    @classmethod
    async def _get_admin_token(cls) -> str:
        """Obtiene un token de acceso usando client_credentials para la API de Admin."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    cls.TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.KEYCLOAK_ADMIN_CLIENT_ID,
                        "client_secret": settings.KEYCLOAK_ADMIN_CLIENT_SECRET
                    }
                )
                response.raise_for_status() 
                return response.json()["access_token"]
        except Exception as e:
            error_message = f"Fallo al autenticar con Keycloak Admin API. Error: {e}"
            print(error_message)
            raise Exception(error_message)


    @staticmethod
    async def create_user(user_data: Dict[str, str]) -> Dict[str, Any]:
        try:
            token = await KeycloakService._get_admin_token()
        except Exception as e:
            return {"created": False, "user_id": None, "error": str(e)}
        kc_user_payload = {
            "username": user_data["email"], 
            "email": user_data["email"],
            "firstName": user_data["name"],
            "lastName": user_data["last_name"],
            "enabled": True,
            "emailVerified": True, 
            "credentials": [
                {
                    "type": "password",
                    "value": user_data["password"],
                    "temporary": False
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                KeycloakService.USERS_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                json=kc_user_payload
            )
            #Aquí retorna el id de keycloak para que la bd intermedia
            #Ejecuten "python inspect_bd.py" y verán el id, solo me falto el de moodle pero no sé porque me marca error
            #No he revisado bien, pero solo falta eso y saber si al meter la pass por la liga de valiar se actualiza en key
            if response.status_code == 201:
                user_id = response.headers.get("Location", "").split('/')[-1]
                return {"created": True, "user_id": user_id, "error": None}
            
            elif response.status_code == 409:
                return {"created": False, "user_id": None, "error": "User already exists in Keycloak (Conflict 409)"}
            
            else:
                error_detail = response.json() if response.content else response.text
                return {"created": False, "user_id": None, "error": f"Keycloak failed with status {response.status_code}. Detail: {error_detail}"}