from pydantic import BaseModel, EmailStr

from app.shared.enums.institutes_enum import InstitutesEnum


class GradeSyncSchema(BaseModel):
    institute: InstitutesEnum | None = None
    course_shortname: str
    email: EmailStr
    assignment_name: str
    score: float


class GradeSyncResponse(BaseModel):
    message: str
    institute_found: str
    details: dict | None = None
