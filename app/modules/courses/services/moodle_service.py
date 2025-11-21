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
            return {
                "courses": [],
                "error": result["error_message"],
            }

        return {
            "courses": result["data"],
            "error": None,
        }
