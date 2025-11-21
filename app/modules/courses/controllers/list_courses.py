from fastapi import HTTPException

from app.modules.courses.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum


class ListCoursesController:
    @staticmethod
    async def list_courses(institute: InstitutesEnum):
        """
        Lista todos los cursos disponibles en la plataforma Moodle para un instituto específico.
        """
        courses = await MoodleService.get_courses(institute=institute)

        if courses["error"]:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_COURSE_LIST_ERROR",
                    "message": courses["error"],
                },
            )

        return courses["courses"]
