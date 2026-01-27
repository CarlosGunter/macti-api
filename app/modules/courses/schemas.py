from pydantic import BaseModel


class CourseResponseSchema(BaseModel):
    id: int
    shortname: str
    fullname: str
    displayname: str
    summary: str
    courseimage: str | None = None


class UserEnrolledCoursesResponseSchema(CourseResponseSchema):
    role: list[str] | None = None
