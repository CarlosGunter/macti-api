from pydantic import BaseModel, ConfigDict, EmailStr

from app.shared.enums.institutes_enum import InstitutesEnum

# si si si roles
from app.shared.models.users_model import AccountStatusEnum


class AccountRequestSchema(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    course_id: int
    institute: InstitutesEnum


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


ListAccountsResponse = list[AccountsResponse]


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


class UserInfoSchema(BaseModel):
    email: EmailStr


class UserInfoResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    last_name: str
    institute: InstitutesEnum
    # Para ORM
    model_config = ConfigDict(from_attributes=True)
