from fastapi import HTTPException

from app.modules.courses.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum


class ListCoursesController:
    @staticmethod
    async def list_courses(
        institute: InstitutesEnum, ids: list[int] | None = None
    ) -> list:
        """
        Lista todos los cursos disponibles en la plataforma Moodle para un instituto específico.
        """
        courses = await MoodleService.get_courses(institute=institute, ids=ids)

        # Cuando se recuperan todos los cursos, Moodle retorna en su primer elemento
        # la misma instancia, se elimina para evitar mostrarla en la lista.
        if ids is None and courses.courses:
            courses.courses = courses.courses[1:]

        if courses.error:
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_COURSE_LIST_ERROR",
                    "message": courses.error,
                },
            )

        return courses.courses
