from fastapi import HTTPException

from app.modules.courses.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum


class UserEnrolledCoursesController:
    """Retorna los cursos en los que un usuario está inscrito."""

    @staticmethod
    async def get_user_enrolled_courses(
        institute: InstitutesEnum, user_id: int
    ) -> list:
        enrolled_courses_result = await MoodleService.get_enrolled_courses(
            institute=institute, user_id=user_id
        )

        if enrolled_courses_result.error:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": f"No se pudieron obtener los cursos inscritos para el usuario {user_id} en {institute}",
                },
            )

        return enrolled_courses_result.enrolled_courses
