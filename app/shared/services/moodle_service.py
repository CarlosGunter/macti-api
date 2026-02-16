"""
Service for interacting with Moodle LMS API - Project MACTI
"""

from types import SimpleNamespace

import httpx

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request


class MoodleService:
    """
    Clase estática que centraliza las operaciones de lectura y escritura en Moodle.
    Incluye gestión de usuarios, inscripciones y creación dinámica de espacios (cursos).
    """

    @staticmethod
    async def get_user_profile_by_email(institute: InstitutesEnum, user_email: str):
        """
        Busca un usuario en el LMS utilizando su dirección de correo electrónico.

        Útil para la sincronización inicial de cuentas cuando el usuario ya existe
        en Moodle pero no en la base de datos local de MACTI.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_get_users_by_field",
            "moodlewsrestformat": "json",
        }
        data = {"field": "email", "values[0]": user_email}

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                user_profile={},
                error=result["error_message"],
            )

        # Moodle retorna una lista; si hay coincidencia, tomamos el primer resultado
        return SimpleNamespace(
            user_profile=result["data"][0] if result["data"] else {},
            error=None,
        )

    @staticmethod
    async def get_user_profile(institute: InstitutesEnum, user_id: int, course_id: int):
        """
        Obtiene el perfil detallado de un usuario dentro del contexto de un curso.

        Este método es clave para recuperar los ROLES (Student, Teacher, etc.)
        que el usuario desempeña en una materia específica.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_get_course_user_profiles",
            "moodlewsrestformat": "json",
        }

        data = {
            "userlist[0][courseid]": course_id,
            "userlist[0][userid]": user_id,
        }

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            data=data,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                user_profile=None,
                error=result["error_message"],
            )

        user_profiles = result["data"]
        user_profile = user_profiles[0] if user_profiles else None

        return SimpleNamespace(
            user_profile=user_profile,
            error=None,
        )

    @staticmethod
    def generate_shortname(institute: InstitutesEnum, fullname: str, group: str) -> str:
        """
        Genera el nombre corto oficial (Subject) siguiendo la lógica del proyecto.
        Ejemplo: CIENCIAS + "Programación" + "G1" -> CIE-PRO-G1
        """
        inst_prefix = str(institute.value)[:3].upper()
        words = fullname.split()

        # Lógica de iniciales: toma la primera letra de las primeras 3 palabras
        if len(words) >= 2:
            course_initials = "".join([word[0] for word in words[:3]]).upper()
        else:
            course_initials = fullname[:3].upper()

        group_suffix = str(group).upper() if group else "0"
        return f"{inst_prefix}-{course_initials}-{group_suffix}"

    @staticmethod
    async def create_course(
        institute: InstitutesEnum,
        fullname: str,
        teacher_name: str,
        group_name: str,
        category_id: int = 1,
    ):
        """
        Automatiza la creación de un nuevo curso en Moodle.
        Genera el shortname automáticamente antes de realizar la petición.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url

        # Generación de nomenclatura oficial
        shortname_gen = MoodleService.generate_shortname(
            institute, fullname, group_name
        )
        display_name = f"{fullname} - {group_name} ({teacher_name})"

        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_course_create_courses",
            "moodlewsrestformat": "json",
        }

        data = {
            "courses[0][fullname]": display_name,
            "courses[0][shortname]": shortname_gen,
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
            return {"created": False, "error": result_response["error_message"]}

        result = result_response["data"]
        return {"created": True, "id": result[0]["id"]}

    @staticmethod
    async def enroll_user(
        user_id: int, course_id: int, institute: InstitutesEnum, role_id: int = 5
    ):
        """
        Matricula a un usuario existente en un curso específico de Moodle.
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
            check_moodle_errors=False,
        )

        if not result_response["success"]:
            return {
                "enrolled": False,
                "error": f"Fallo de conexión/petición: {result_response['error_message']}",
            }

        result = result_response["data"]

        if isinstance(result, dict) and "exception" in result:
            if result.get("message") == "error/Message was not sent.":
                return {
                    "user_id": user_id,
                    "course_id": course_id,
                    "enrolled": True,
                    "warning": "Matrícula exitosa con error de notificación SMTP",
                }
            return {
                "enrolled": False,
                "error": f"Error de Moodle: {result.get('message')}",
            }

        return {"user_id": user_id, "course_id": course_id, "enrolled": True}

    @staticmethod
    async def delete_user(user_id, institute: InstitutesEnum):
        """
        Elimina a un usuario en Moodle usando httpx.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_delete_users",
            "moodlewsrestformat": "json",
        }
        data = {"userids[0]": str(user_id)}

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, params=params, data=data)
            response.raise_for_status()
            result = response.json()

        if isinstance(result, dict) and "exception" in result:
            raise Exception(f"Error deleting user in Moodle: {result}")

        return {"deleted": True, "user_id": user_id}
