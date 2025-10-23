from pydantic import BaseModel, EmailStr
from typing import Literal
from enum import Enum

class InstituteEnum(str, Enum):
    principal = "principal"
    cuantico = "cuantico"
    ciencias = "ciencias"
    ingenieria = "ingenieria"
    encit = "encit"
    ier = "ier"
    enes_m = "enes_m"
    hpc = "hpc"
    igf = "igf"
    ene = "ene"

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