from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    from app.shared.models.auth_model import Auth


class StudentCourseRequest(Base):
    __tablename__ = "MCT_student_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    auth_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_auth.id", ondelete="CASCADE"), nullable=False
    )

    moodle_course_id: Mapped[int] = mapped_column(Integer, nullable=True)

    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum), nullable=False
    )

    auth: Mapped["Auth"] = relationship("Auth", back_populates="moodle_courses")

    def __repr__(self):
        return f"<StudentCourseRequest(auth_id={self.auth_id}, moodle_course_id={self.moodle_course_id}, status={self.status.value})>"
