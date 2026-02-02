from types import SimpleNamespace

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request


class MoodleService:
    @staticmethod
    async def get_courses(institute: InstitutesEnum, ids: list[int] | None = None):
        """
        Obtener la lista de cursos desde Moodle según el instituto.
        """
        config = MOODLE_CONFIG[institute]
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_course_get_courses",
            "moodlewsrestformat": "json",
        }

        data = {} if ids else None
        for i, course_id in enumerate(ids or []):
            if data is not None:
                data[f"options[ids][{i}]"] = course_id

        result = await make_moodle_request(
            url=config.moodle_url,
            params=params,
            institute=institute,
            data=data,
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
