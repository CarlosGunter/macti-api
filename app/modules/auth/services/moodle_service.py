"""
Service for interacting with Moodle LMS API
"""

import httpx
from app.core.config import settings

class MoodleService:
    MOODLE_URL = settings.MOODLE_URL
    MOODLE_TOKEN = settings.MOODLE_TOKEN

    @staticmethod
    async def create_user(user_data):
        """
        Create a user in Moodle using the REST API.
        """
        print({
            "MoodleService.MOODLE_TOKEN": MoodleService.MOODLE_TOKEN,
            "MoodleService.MOODLE_URL": MoodleService.MOODLE_URL
        })

        endpoint = MoodleService.MOODLE_URL
        params = {
            "wstoken": MoodleService.MOODLE_TOKEN,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "users[0][username]": user_data["email"].split("@")[0],
            "users[0][password]": user_data.get("password", "Password1234"),
            "users[0][firstname]": user_data.get("name", "User"),
            "users[0][lastname]": user_data.get("last_name", "NA"),
            "users[0][email]": user_data["email"],
            "users[0][auth]": "manual",
            "users[0][country]": "MX",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(endpoint, params=params, data=data)
                response.raise_for_status()
                try:
                    result = response.json()
                except Exception as e:
                    print(f"Error al parsear JSON de Moodle: {e}")
                    return {"error": "Respuesta no válida del servidor Moodle", "created": False}
        except httpx.RequestError as e:
            print(f"Error de conexión con Moodle: {e}")
            return {"error": "No se pudo conectar con Moodle", "created": False}
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP al crear usuario en Moodle: {e}")
            return {"error": f"HTTP error: {e.response.status_code}", "created": False}
        except Exception as e:
            print(f"Error inesperado al crear usuario: {e}")
            return {"error": str(e), "created": False}

        # Validar si Moodle devolvió un error
        if isinstance(result, dict) and "exception" in result:
            print("Moodle API returned an exception:", result)
            return {"error": result, "created": False}

        return {**result[0], "created": True} if isinstance(result, list) else {"result": result, "created": True}

    @staticmethod
    async def enroll_user(user_id, course_id):
        """
        Enroll a user in a Moodle course using the REST API.
        """
        endpoint = MoodleService.MOODLE_URL
        params = {
            "wstoken": MoodleService.MOODLE_TOKEN,
            "wsfunction": "enrol_manual_enrol_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "enrolments[0][roleid]": 5,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
            "enrolments[0][timestart]": 0,
            "enrolments[0][timeend]": 0,
            "enrolments[0][suspend]": 0,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(endpoint, params=params, data=data)
                response.raise_for_status()
                result = response.json()
        except httpx.RequestError as e:
            print(f"Error de conexión con Moodle (enroll_user): {e}")
            return {"error": "No se pudo conectar con Moodle", "enrolled": False}
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP al inscribir usuario en Moodle: {e}")
            return {"error": f"HTTP error: {e.response.status_code}", "enrolled": False}
        except Exception as e:
            print(f"Error inesperado al inscribir usuario: {e}")
            return {"error": str(e), "enrolled": False}

        print("DEBUG Moodle response (enroll_user):", result)

        if isinstance(result, dict) and "exception" in result:
            if result.get("message") == "error/Message was not sent.":
                print("Moodle no envió correo, pero el usuario fue inscrito")
                return {
                    "user_id": user_id,
                    "course_id": course_id,
                    "enrolled": True,
                    "warning": result
                }
            return {"error": result, "enrolled": False}

        return {"user_id": user_id, "course_id": course_id, "enrolled": True}
