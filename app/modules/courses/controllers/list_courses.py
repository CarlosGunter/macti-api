from app.modules.courses.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum


class ListCoursesController:
    @staticmethod
    async def list_courses(institute: InstitutesEnum):
        """
        Lista todos los cursos disponibles en la plataforma Moodle para un instituto específico.
        """
        courses = await MoodleService.get_courses(institute=institute)

        return courses
