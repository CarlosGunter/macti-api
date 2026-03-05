"""
Service for interacting with Moodle LMS API
"""

from types import SimpleNamespace

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_moodle_enum import RoleEnum
from app.shared.services.moodle_client import make_moodle_request
from app.shared.services.moodle_service import MoodleService as BaseMoodleService


class MoodleService:
    """
    Clase estática que centraliza las operaciones de lectura y escritura en Moodle.
    """

    @staticmethod
    async def create_user(user_data: dict, institute: InstitutesEnum):
        """
        Crea un nuevo usuario en la instancia de Moodle correspondiente.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
        }

        # Estructura de datos requerida por el Web Service de Moodle
        data = {
            "users[0][username]": user_data["email"],
            "users[0][firstname]": user_data.get("name", "User"),
            "users[0][lastname]": user_data.get("last_name", "NA"),
            "users[0][email]": user_data["email"],
            "users[0][auth]": "oauth2",
        }

        print(
            f"DEBUG: Enviando creación de usuario a Moodle ({institute.value}): {user_data['email']}"
        )

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
        )

        if not result_response["success"]:
            return {
                "created": False,
                "error": result_response["error_message"],
            }

        result = result_response["data"]

        # Moodle retorna una lista de diccionarios con los IDs de los usuarios creados.
        # Se extrae el 'id' del primer elemento (index 0).
        return {"created": True, "id": result[0]["id"]}

    @staticmethod
    async def enroll_user(
        user_id: int, course_id: int, institute: InstitutesEnum, role_id: int = 5
    ):
        """
        Matricula a un usuario existente en un curso específico de Moodle con un rol dinámico.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "enrol_manual_enrol_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "enrolments[0][roleid]": role_id,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
            "enrolments[0][timestart]": 0,
            "enrolments[0][timeend]": 0,
            "enrolments[0][suspend]": 0,
        }

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
            # Se desactiva la verificación automática para manejar excepciones manualmente abajo
            check_moodle_errors=False,
        )

        if not result_response["success"]:
            return {
                "enrolled": False,
                "error": f"Fallo de conexión/petición: {result_response['error_message']}",
            }

        result = result_response["data"]

        # Manejo de Excepciones de Moodle:
        # Moodle puede retornar un 200 OK pero con un cuerpo de 'exception'.
        if isinstance(result, dict) and "exception" in result:
            if result.get("message") == "error/Message was not sent.":
                print(
                    f"AVISO: Usuario {user_id} matriculado, pero Moodle no pudo enviar el email de aviso."
                )
                return {
                    "user_id": user_id,
                    "course_id": course_id,
                    "enrolled": True,
                    "warning": "Matrícula exitosa con error de notificación SMTP en Moodle",
                }

            return {
                "enrolled": False,
                "error": f"Error de Moodle: {result.get('message', 'Desconocido')}",
            }

        return {"user_id": user_id, "course_id": course_id, "enrolled": True}

    @staticmethod
    async def delete_user(user_id, institute: InstitutesEnum):
        """
        Delete a user in Moodle using the REST API.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_delete_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "userids[0]": str(user_id),
        }

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
        )

        if not result_response["success"]:
            return {
                "deleted": False,
                "error": result_response["error_message"],
            }

        return {"deleted": True, "user_id": user_id}

    @staticmethod
    async def get_user_roles(
        institute: InstitutesEnum,
        course_id: int,
        moodle_id: int,
    ) -> list[RoleEnum]:
        """
        Función auxiliar para recuperar roles asignados en un curso de Moodle.
        """

        get_user_profile_result = await BaseMoodleService.get_user_profile(
            institute=institute, user_id=moodle_id, course_id=course_id
        )

        if get_user_profile_result.error:
            return []

        user_roles = get_user_profile_result.user_profile.get("roles", [])

        # Conversión de IDs numéricos de Moodle al Enum RoleEnum para tipado fuerte
        list_roles = [RoleEnum(role["roleid"]) for role in user_roles]

        return list_roles

    @staticmethod
    async def create_course(
        institute: InstitutesEnum,
        fullname: str,
        teacher_name: str,
        group_name: str,
        shortname: str,
        category_id: int = 1,
    ):
        """
        Automatiza la creación de un nuevo curso en Moodle.
        Genera el shortname automáticamente antes de realizar la petición.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url

        display_name = f"{fullname} - {group_name} ({teacher_name})"

        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_course_create_courses",
            "moodlewsrestformat": "json",
        }

        data = {
            "courses[0][fullname]": display_name,
            "courses[0][shortname]": shortname,
            "courses[0][categoryid]": category_id,
            "courses[0][idnumber]": group_name,
            "courses[0][summary]": f"Docente: {teacher_name}",
            "courses[0][format]": "topics",
        }

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
        )

        if not result_response["success"]:
            return SimpleNamespace(course=None, error=result_response["error_message"])

        # Moodle retorna una lista; extraemos el primer curso creado
        return SimpleNamespace(course=result_response["data"][0], error=None)
