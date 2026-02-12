from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.shared.models.users_model import UserAccounts


class Course(Base):
    __tablename__ = "MCT_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    users: Mapped[list["UserAccounts"]] = relationship(
        "UserAccounts", back_populates="course"
    )

    def __repr__(self):
        return f"<Course(name='{self.name}')>"
