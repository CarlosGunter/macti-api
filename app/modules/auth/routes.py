# Módulo APIRouter de Autenticación y Registro - Proyecto MACTI
# Este archivo define las rutas para el flujo de solicitudes, aprobación y
# creación definitiva de cuentas de usuario.

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.controllers.get_user_info import GetUserInfoController
from app.shared.dependecies.get_current_user import get_current_user
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum

from ...shared.enums.status_enum import AccountStatusEnum
from .controllers.change_status import ChangeStatusController
from .controllers.create_account import CreateAccountController
from .controllers.list_account_requests import ListAccountRequestsController
from .controllers.request_account import RequestAccountController
from .schema import (
    AccountRequestResponse,
    ConfirmAccountResponse,
    ConfirmAccountSchema,
    CreateAccountResponse,
    CreateAccountSchema,
    ListAccountsResponse,
    StudentRequestSchema,
    TeacherRequestSchema,
    UserInfoResponse,
)

# Definición del router con el prefijo /auth para agrupar lógica de identidad
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/request-account/student",
    summary="Crear una solicitud de cuenta para ALUMNO",
    description="Endpoint para que un alumno solicite su acceso.",
    response_model=AccountRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_student_account(
    body_info: StudentRequestSchema, db: Session = Depends(get_db)
):
    # El controlador es síncrono (sin await)
    return RequestAccountController.request_account(
        role=AccountRoleEnum.ALUMNO, data=body_info, db=db
    )


@router.post(
    "/request-account/teacher",
    summary="Crear una solicitud de cuenta para DOCENTE",
    description="Endpoint para que un docente solicite acceso.",
    response_model=AccountRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_teacher_account(
    body_info: TeacherRequestSchema, db: Session = Depends(get_db)
):
    # El controlador es síncrono (sin await)
    return RequestAccountController.request_account(
        role=AccountRoleEnum.DOCENTE, data=body_info, db=db
    )


@router.get(
    "/list-account-requests",
    summary="Listar solicitudes de cuenta por curso",
    response_model=ListAccountsResponse,
)
async def list_accounts_requests(
    course_id: int = Query(..., description="ID del curso en Moodle"),
    institute: InstitutesEnum = Query(..., description="Instituto"),
    status: AccountStatusEnum | None = Query(None),
    db=Depends(get_db),
    user_info=Depends(get_current_user),
):
    return await ListAccountRequestsController.list_accounts_requests(
        db=db,
        course_id=course_id,
        institute=institute,
        status=status,
        user_info=user_info,
    )


@router.patch(
    "/change-status",
    summary="Cambiar estatus de una cuenta",
    response_model=ConfirmAccountResponse,
)
async def confirm_account(body_info: ConfirmAccountSchema, db=Depends(get_db)):
    return await ChangeStatusController.change_status(data=body_info, db=db)


@router.get(
    "/user-info-by-token",
    summary="Obtener info de usuario por token",
    response_model=UserInfoResponse,
)
def confirm_email(token: str = Query(...), db=Depends(get_db)):
    return GetUserInfoController.get_user_info(token=token, db=db)


@router.post(
    "/create-account",
    summary="Finalizar creación de cuenta",
    response_model=CreateAccountResponse,
)
async def create_account(body_info: CreateAccountSchema, db=Depends(get_db)):
    # El controlador es asíncrono (usa await)
    return await CreateAccountController.create_account(data=body_info, db=db)
