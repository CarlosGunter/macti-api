from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    from app.shared.models.users_model import UserAccounts


class UserCourses(Base):
    __tablename__ = "MCT_user_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_user_accounts.id"), nullable=False
    )

    course_full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    groups: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    owner_user: Mapped["UserAccounts"] = relationship(
        "UserAccounts", back_populates="assigned_courses"
    )

    def __repr__(self):
        return f"<UserCourse(course='{self.course_full_name}', status='{self.status.value}')>"
