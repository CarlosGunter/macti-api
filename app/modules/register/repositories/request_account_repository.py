from typing import cast

from sqlalchemy.orm import Session

from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.auth_model import Auth
from app.shared.models.student_courses_model import StudentCourseRequest
from app.shared.models.teacher_courses_model import TeacherCourseRequest
from app.shared.models.user_profiles_model import UserProfile

from ..schemas import StudentRequestSchema, TeacherRequestSchema


class RequestAccountRepository:
    """Encapsula la persistencia del flujo de solicitud de cuenta."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email_and_institute(
        self, email: str, institute: InstitutesEnum
    ) -> Auth | None:
        return (
            self.db.query(Auth)
            .filter(Auth.email == email, Auth.institute == institute)
            .one_or_none()
        )

    def create_account_request(
        self,
        role: AccountRoleEnum,
        data: StudentRequestSchema | TeacherRequestSchema,
    ) -> Auth:
        db_request = Auth(
            email=data.email,
            institute=data.institute,
            is_active=False,
        )
        self.db.add(db_request)
        self.db.flush()

        profile = UserProfile(
            auth_id=db_request.id,
            name=data.name,
            last_name=data.last_name,
            status=AccountStatusEnum.PENDING,
        )
        self.db.add(profile)

        if role == AccountRoleEnum.ALUMNO:
            student_data = cast(StudentRequestSchema, data)
            student_course_request = StudentCourseRequest(
                auth_id=db_request.id,
                moodle_course_id=student_data.course_id,
                status=AccountStatusEnum.PENDING,
            )
            self.db.add(student_course_request)

        elif role == AccountRoleEnum.DOCENTE:
            teacher_data = cast(TeacherRequestSchema, data)
            teacher_course_request = TeacherCourseRequest(
                auth_id=db_request.id,
                course_full_name=teacher_data.course_full_name,
                groups=",".join(teacher_data.groups) if teacher_data.groups else None,
                status=AccountStatusEnum.PENDING,
            )
            self.db.add(teacher_course_request)

        return db_request

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity: Auth) -> None:
        self.db.refresh(entity)

    def rollback(self) -> None:
        self.db.rollback()
