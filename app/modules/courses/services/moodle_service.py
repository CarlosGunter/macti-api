from types import SimpleNamespace

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request


class MoodleService:
    @staticmethod
    async def get_courses(institute: InstitutesEnum):
        """
        Obtener la lista de cursos desde Moodle según el instituto.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_course_get_courses",
            "moodlewsrestformat": "json",
        }

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            institute=institute,
        )

        if not result["success"]:
            return SimpleNamespace(
                courses=[],
                error=result["error_message"],
            )

        return SimpleNamespace(
            courses=result["data"],
            error=None,
        )

    @staticmethod
    async def get_enrolled_courses(institute: InstitutesEnum, user_id: int):
        """
        Obtener los cursos en los que un usuario está inscrito en Moodle.
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
    async def get_user_profile(institute: InstitutesEnum, user_id: int, course_id: int):
        """
        Obtener el perfil de un usuario en un curso específico de Moodle.
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
