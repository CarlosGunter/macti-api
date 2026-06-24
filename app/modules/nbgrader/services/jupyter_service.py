import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class JupyterService:
    @staticmethod
    async def sync_user_role(
        email: str,
        role: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ):
        """
        Sincroniza el rol del usuario en JupyterHub e inyecta metadatos (nombres)
        en el campo user_data para que la librería macti.eval pueda consumirlos.
        """
        import os

        from dotenv import load_dotenv

        load_dotenv()

        token = os.getenv("JUPYTER_TOKEN_PRINCIPAL")
        api_base_url = "https://tlapoa.lamod.unam.mx/hubier/hub/api"
        group_name = "formgrade-course"

        headers = {"Authorization": f"token {token}"}
        print(f"🕵️‍♂️ VERIFICANDO TOKEN EN FASTAPI: {headers['Authorization'][:15]}...")

        # Construimos el cuerpo de la petición. Si vienen nombres, se los pasamos a JupyterHub
        user_payload: dict[str, Any] = {}
        if first_name or last_name:
            user_payload["user_data"] = {
                "first_name": first_name or "",
                "last_name": last_name or "",
            }

        async with httpx.AsyncClient(verify=False) as client:
            try:
                await client.post(
                    f"{api_base_url}/users/{email}", json=user_payload, headers=headers
                )
                await client.post(
                    f"{api_base_url}/groups/{group_name}", json={}, headers=headers
                )
            except Exception as e:
                print(f"⚠️ Jupyter Pre-Check: {str(e)}")

        if role == "docente" or "docente" in str(role).lower():
            url = f"{api_base_url}/groups/{group_name}/users"

            async with httpx.AsyncClient(verify=False) as client_group:
                try:
                    res = await client_group.post(
                        url, json={"users": [str(email)]}, headers=headers
                    )

                    print("==============================================")
                    print("📡 RESPUESTA API JUPYTER (PASO C - AISLADO):")
                    print(f"   -> Usuario: {email}")
                    print(f"   -> Status Code: {res.status_code}")
                    print(f"   -> Body devuelto: {res.text}")
                    print("==============================================")
                    return res.status_code in [200, 201]
                except Exception as e:
                    print(f"❌ Error en Paso C Aislado: {str(e)}")
                    return False
        else:
            url = f"{api_base_url}/groups/{group_name}/users"
            async with httpx.AsyncClient(verify=False) as client_del:
                await client_del.request(
                    "DELETE", url, json={"users": [str(email)]}, headers=headers
                )
            return True

    @staticmethod
    async def get_user_info(username: str):
        """
        Consulta directamente a la API de JupyterHub para obtener
        el estado real de un usuario.
        """
        import os

        from dotenv import load_dotenv

        load_dotenv()

        token = os.getenv("JUPYTER_TOKEN_PRINCIPAL")
        api_base_url = "https://tlapoa.lamod.unam.mx/hubier/hub/api"
        headers = {"Authorization": f"token {token}"}

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.get(
                    f"{api_base_url}/users/{username}", headers=headers
                )
                if response.status_code == 200:
                    return response.json()
                return {
                    "error": "Usuario no encontrado en Jupyter",
                    "status": response.status_code,
                }
            except Exception as e:
                return {"error": str(e)}

    @staticmethod
    async def get_all_users_status(db_users: list):
        """
        Recibe una lista de usuarios de la DB y consulta su estado en Jupyter
        """
        import os

        from dotenv import load_dotenv

        load_dotenv()

        token = os.getenv("JUPYTER_TOKEN_PRINCIPAL")
        api_base_url = "https://tlapoa.lamod.unam.mx/hubier/hub/api"
        headers = {"Authorization": f"token {token}"}

        summary = []
        async with httpx.AsyncClient(verify=False) as client:
            for user in db_users:
                try:
                    # 1. Consultamos a la API de JupyterHub
                    res = await client.get(
                        f"{api_base_url}/users/{user.email}", headers=headers
                    )
                    jupyter_data = res.json() if res.status_code == 200 else {}

                    # 2. Obtenemos el rol de forma segura
                    user_role = "No asignado"
                    if hasattr(user, "profile") and user.profile:
                        user_role = getattr(user.profile, "role", "No asignado")
                    elif hasattr(user, "role"):
                        user_role = user.role

                    summary.append(
                        {
                            "email": user.email,
                            "rol_sistema": str(user_role),
                            "grupos_jupyter": jupyter_data.get(
                                "groups", ["No encontrado en Jupyter"]
                            ),
                            "admin_en_jupyter": jupyter_data.get("admin", False),
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"❌ ERROR CRUCIAL JUPYTER para {user.email}: {str(e)}"
                    )
                    summary.append(
                        {
                            "email": user.email,
                            "error": f"Fallo interno en el backend: {str(e)}",
                        }
                    )
        return summary
