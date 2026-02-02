from pydantic import BaseModel, ConfigDict, EmailStr

from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.models.users_model import AccountStatusEnum


class AccountBaseSchema(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    institute: InstitutesEnum


class StudentRequestSchema(AccountBaseSchema):
    course_id: int


class TeacherRequestSchema(AccountBaseSchema):
    course_full_name: str
    course_key: str
    groups: str | None = None
    course_id: int | None = None


class AccountRequestResponse(BaseModel):
    message: str
    model_config = ConfigDict(from_attributes=True)


class AccountsResponse(BaseModel):
    id: int
    name: str
    last_name: str
    email: EmailStr
    status: AccountStatusEnum
    model_config = ConfigDict(from_attributes=True)


ListAccountsResponse = list[AccountsResponse]


class ConfirmAccountSchema(BaseModel):
    id: int
    status: AccountStatusEnum


class ConfirmAccountResponse(BaseModel):
    message: str
    model_config = ConfigDict(from_attributes=True)


class CreateAccountSchema(BaseModel):
    user_id: int
    new_password: str


class CreateAccountResponse(BaseModel):
    message: str
    model_config = ConfigDict(from_attributes=True)


class UserInfoResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    last_name: str
    institute: InstitutesEnum
    model_config = ConfigDict(from_attributes=True)
