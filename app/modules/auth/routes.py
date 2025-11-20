from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.modules.auth.controllers.get_user_info import GetUserInfoController
from app.shared.enums.institutes_enum import InstitutesEnum

from .controllers.change_status import ChangeStatusController
from .controllers.create_account import CreateAccountController
from .controllers.list_account_requests import ListAccountRequestsController
from .controllers.request_account import RequestAccountController
from .enums import AccountStatusEnum
from .schema import (
    AccountRequestResponse,
    AccountRequestSchema,
    ConfirmAccountResponse,
    ConfirmAccountSchema,
    CreateAccountResponse,
    CreateAccountSchema,
    ListAccountsResponse,
    UserInfoResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# Crear solicitud de cuenta
@router.post(
    "/request-account",
    summary="Crear una solicitud de cuenta",
    response_model=AccountRequestResponse,
)
async def request_account(body_info: AccountRequestSchema, db=Depends(get_db)):
    return RequestAccountController.request_account(data=body_info, db=db)


# Listar solicitudes por curso
@router.get(
    "/list-account-requests",
    summary="Endpoint que se encarga de listar todas las solicitudes de cuenta de acurdo a un curso",
    description="Las solicitudes de cuenta se listan desde el perfil del profesor de un curso",
    response_model=ListAccountsResponse,
)
async def list_accounts_requests(
    course_id: int = Query(description="Filtra las solicitudes por ID de curso"),
    institute: InstitutesEnum = Query(
        ..., description="Filtra las solicitudes por instituto"
    ),
    status: AccountStatusEnum | None = Query(
        None, description="Filtra las solicitudes por estatus"
    ),
    db=Depends(get_db),
):
    return ListAccountRequestsController.list_accounts_requests(
        db=db,
        course_id=course_id,
        institute=institute,
        status=status,
    )


@router.patch(
    "/change-status",
    summary="Cambiar estado de solicitud de una cuenta",
    response_model=ConfirmAccountResponse,
)
async def confirm_account(body_info: ConfirmAccountSchema, db=Depends(get_db)):
    return await ChangeStatusController.change_status(data=body_info, db=db)


@router.get(
    "/user-info-by-token",
    summary="Obtener información del usuario mediante token de email",
    response_model=UserInfoResponse,
)
def confirm_email(
    token: str = Query(
        ..., description="Token de email para obtener datos del usuario"
    ),
    db=Depends(get_db),
):
    return GetUserInfoController.get_user_info(token=token, db=db)


@router.post(
    "/create-account",
    summary="Crear cuenta en Keycloak y Moodle",
    response_model=CreateAccountResponse,
)
async def create_account(body_info: CreateAccountSchema, db=Depends(get_db)):
    return await CreateAccountController.create_account(data=body_info, db=db)
