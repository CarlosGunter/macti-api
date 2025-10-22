from pydantic import BaseModel, EmailStr
from typing import Literal, List


class AccountRequestSchema(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    course_id: int

# Response model para listar solicitudes (usable como response_model)
class AccountRequestResponse(BaseModel):
    id: int
    name: str
    last_name: str
    email: EmailStr
    status: Literal["pending", "approved", "rejected", "created"]

    class Config:
        orm_mode = True
        
AccountRequestResponseList = List[AccountRequestResponse]


class ConfirmAccountSchema(BaseModel):
    id: int
    status: Literal["pending", "approved", "rejected"]


class CreateAccountSchema(BaseModel):
    user_id: int
    new_password: str


class EmailValidationSchema(BaseModel):
    email: EmailStr
