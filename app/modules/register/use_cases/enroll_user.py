from dataclasses import dataclass

from app.modules.register.services.moodle_service import MoodleService
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.role_moodle_enum import RoleEnum
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest


@dataclass
class EnrollUserResult:
    enrolled: bool
    error: str | None = None


class EnrollUserUseCase:
    """Orquesta la inscripción de un usuario en un curso"""

    def __init__(self, moodle_service: MoodleService, institute: InstitutesEnum):
        self.moodle_service = moodle_service
        self.institute = institute

    async def execute(
        self, request_course_data: TeacherCourseRequest | StudentCourseRequest
    ) -> EnrollUserResult:
        """Ejecuta el flujo de inscripción de un usuario en un curso específico"""

        role = (
            request_course_data.auth.profile.role
            if request_course_data.auth and request_course_data.auth.profile
            else None
        )
        if role is None:
            return EnrollUserResult(
                enrolled=False, error="Falta información de rol en la solicitud"
            )

        course_ids: list[int] = []

        if (
            isinstance(request_course_data, StudentCourseRequest)
            and request_course_data.moodle_course_id is not None
        ):
            course_ids = [request_course_data.moodle_course_id]

        # Para docentes, primero se crean los cursos
        if isinstance(request_course_data, TeacherCourseRequest):
            course_ids = (
                await self._create_courses(request_course_data=request_course_data)
                or []
            )
            if not course_ids:
                return EnrollUserResult(
                    enrolled=False, error="Error al crear cursos en Moodle"
                )

        if not course_ids:
            return EnrollUserResult(
                enrolled=False,
                error="No se pudo determinar el ID del curso para la inscripción",
            )

        moodle_role = self._get_moodle_role_from_account(role)

        for course_id in course_ids:
            enrolled = await self.moodle_service.enroll_user(
                request_course_data.auth_id, course_id, self.institute, moodle_role
            )

            if not enrolled.enrolled:
                return EnrollUserResult(enrolled=False, error=enrolled.error)

        return EnrollUserResult(enrolled=True, error=None)

    def _get_moodle_role_from_account(self, role: AccountRoleEnum) -> RoleEnum:
        """Mapea el rol de la aplicación al rol correspondiente en Moodle"""

        if role == AccountRoleEnum.ALUMNO:
            return RoleEnum.STUDENT
        if role == AccountRoleEnum.DOCENTE:
            return RoleEnum.TEACHER

    async def _create_courses(
        self, request_course_data: TeacherCourseRequest
    ) -> list[int] | None:
        """Crea cursos en Moodle basado en la información de la solicitud"""

        groups_list = [
            g.strip() for g in request_course_data.groups.split(",") if g.strip()
        ]
        if not groups_list:
            groups_list = ["General"]

        course_creation_result = await self.moodle_service.create_courses(
            institute=self.institute,
            fullname=request_course_data.course_full_name,
            groups=groups_list,
        )
        if course_creation_result.error:
            return None

        return course_creation_result.course_ids
