from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr

from app.modules.auth.models import AccountStatusEnum

from .models import InstituteEnum


class AccountRequestSchema(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    course_id: int
    institute: InstituteEnum


class AccountRequestResponse(BaseModel):
    message: str
    # Para ORM
    model_config = ConfigDict(from_attributes=True)


class AccountsResponse(BaseModel):
    id: int
    name: str
    last_name: str
    email: EmailStr
    status: AccountStatusEnum
    # Para ORM
    model_config = ConfigDict(from_attributes=True)


ListAccountsResponse = List[AccountsResponse]


class ConfirmAccountSchema(BaseModel):
    id: int
    status: AccountStatusEnum


class ConfirmAccountResponse(BaseModel):
    message: str
    # Para ORM
    model_config = ConfigDict(from_attributes=True)


class CreateAccountSchema(BaseModel):
    user_id: int
    new_password: str


class CreateAccountResponse(BaseModel):
    message: str
    # Para ORM
    model_config = ConfigDict(from_attributes=True)


class EmailValidationSchema(BaseModel):
    email: EmailStr


class EmailValidationResponse(BaseModel):
    id: int
    email: EmailStr
    # Para ORM
    model_config = ConfigDict(from_attributes=True)
