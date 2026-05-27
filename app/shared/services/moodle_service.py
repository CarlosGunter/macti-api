"""
Service for interacting with Moodle LMS API - Project MACTI
"""

from types import SimpleNamespace

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
    async def get_enrolled_courses(institute: InstitutesEnum, user_id: int):
        """
        Consulta los cursos en los que un usuario específico está inscrito.

        A diferencia del listado global, esta consulta ('core_enrol_get_users_courses')
        requiere un 'userid' y retorna únicamente los cursos vinculados a ese perfil.

        Retorna:
            SimpleNamespace: Con los atributos .enrolled_courses (lista) y .error (str o None).
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_enrol_get_users_courses",
            "moodlewsrestformat": "json",
            "userid": user_id,
        }

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                enrolled_courses=[],
                error=result["error_message"],
            )

        return SimpleNamespace(
            enrolled_courses=result["data"],
            error=None,
        )

    @staticmethod
    async def is_user_enrolled_in_course(
        institute: InstitutesEnum, user_id: int, course_id: int
    ):
        """
        Verifica si un usuario ya está inscrito en un curso específico de Moodle.

        Retorna:
            SimpleNamespace: Con los atributos .is_enrolled (bool) y .error (str o None).
        """
        enrolled_courses_result = await MoodleService.get_enrolled_courses(
            institute=institute, user_id=user_id
        )

        if enrolled_courses_result.error:
            return SimpleNamespace(
                is_enrolled=False, error=enrolled_courses_result.error
            )

        enrolled_courses = getattr(enrolled_courses_result, "enrolled_courses", [])

        for course in enrolled_courses:
            if not isinstance(course, dict):
                continue

            enrolled_course_id = course.get("id", course.get("courseid"))
            if enrolled_course_id is None:
                continue

            if int(enrolled_course_id) == int(course_id):
                return SimpleNamespace(is_enrolled=True, error=None)

        return SimpleNamespace(is_enrolled=False, error=None)
