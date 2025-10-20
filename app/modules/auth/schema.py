from pydantic import BaseModel, EmailStr
from typing import Literal

class AccountRequestSchema(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    course_id: int

class ConfirmAccountSchema(BaseModel):
    id: int
    status: Literal["pending", "approved", "rejected"]

class CreateAccountSchema(BaseModel):
    user_id: int
    new_password: str


class EmailValidationSchema(BaseModel):
    email: EmailStr