from pydantic import BaseModel, EmailStr
from typing import Literal
from .models import InstituteEnum

class AccountRequestSchema(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    course_id: int
    institute: InstituteEnum
class ConfirmAccountSchema(BaseModel):
    id: int
    status: Literal["pending", "approved", "rejected"]

class CreateAccountSchema(BaseModel):
    user_id: int
    new_password: str


class EmailValidationSchema(BaseModel):
    email: EmailStr