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
