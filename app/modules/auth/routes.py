from fastapi import APIRouter, Depends, Query
from app.core.database import get_db
from .controllers.request_account import RequestAccountController
from .controllers.list_account_requests import ListAccountRequestsController
from .controllers.change_status import ChangeStatusController
from .controllers.create_account import CreateAccountController
from .schema import (
    AccountRequestResponse,
    AccountRequestSchema,
    ConfirmAccountResponse,
    ConfirmAccountSchema,
    CreateAccountResponse,
    CreateAccountSchema,
    EmailValidationResponse,
    ListAccountsResponse,
)
from app.modules.auth.services.email_service import EmailService

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
    "/list-accounts-requests",
    summary="Endpoint que se encarga de listar todas las solicitudes de cuenta de acurdo a un curso",
    description="Las solicitudes de cuenta se listan desde el perfil del profesor de un curso",
    response_model=ListAccountsResponse,
)
async def list_accounts_requests(
    course_id: int = Query(description="Filtra las solicitudes por ID de curso"),
    db=Depends(get_db),
):
    return ListAccountRequestsController.list_accounts_requests(
        db=db, course_id=course_id
    )


# Aprobar o rechazar solicitud y enviar correo
@router.patch(
    "/confirm-account",
    summary="Aprobar o rechazar solicitud y enviar correo",
    response_model=ConfirmAccountResponse,
)
async def confirm_account(body_info: ConfirmAccountSchema, db=Depends(get_db)):
    return await ChangeStatusController.change_status(data=body_info, db=db)


# Crear cuenta en Keycloak y Moodle
# es este dónde se recibe la pass nueva para actulizar el key
@router.post(
    "/create-account",
    summary="Crear cuenta en Keycloak y Moodle",
    response_model=CreateAccountResponse,
)
async def create_account(body_info: CreateAccountSchema, db=Depends(get_db)):
    return await CreateAccountController.create_account(data=body_info, db=db)


# Confirmar datos token
@router.get(
    "/confirmacion",
    summary="Confirmar email con token",
    response_model=EmailValidationResponse,
)
def confirm_email(token: str):
    return EmailService.validate_token(token)
