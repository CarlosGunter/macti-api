# Módulo APIRouter de Autenticación y Registro - Proyecto MACTI
# Este archivo define las rutas para el flujo de solicitudes, aprobación y
# creación definitiva de cuentas de usuario.

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.register.controllers.create_account import CreateAccountController
from app.modules.register.controllers.get_user_info import GetUserInfoController
from app.modules.register.controllers.update_request_status import (
    RequestStatusController,
)
from app.shared.enums.role_enum import AccountRoleEnum

from .controllers.account_requests import AccountRequestsController
from .schemas import (
    AccountRequestResponse,
    CreateAccountResponse,
    CreateAccountSchema,
    RequestStatusUpdateResponseSchema,
    RequestStatusUpdateSchema,
    StudentRequestSchema,
    TeacherRequestSchema,
    UserInfoResponse,
)

# Definición del router con el prefijo /register para agrupar lógica de registro
router = APIRouter(prefix="/register", tags=["Registro"])


@router.post(
    "/request-account/student",
    summary="Crear una solicitud de cuenta para ALUMNO",
    description="Endpoint para que un alumno solicite su acceso.",
    response_model=AccountRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_student_account(
    body_info: StudentRequestSchema,
    db: Annotated[Session, Depends(get_db)],
):
    return await AccountRequestsController.request_account(
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
    body_info: TeacherRequestSchema,
    db: Annotated[Session, Depends(get_db)],
):
    return await AccountRequestsController.request_account(
        role=AccountRoleEnum.DOCENTE, data=body_info, db=db
    )


@router.patch(
    "/update-request-status/{role}",
    summary="Cambiar estatus de una solicitud",
    description="Endpoint para que el administrador pueda aprobar/rechazar solicitudes de cuenta.",
    response_model=RequestStatusUpdateResponseSchema,
)
async def update_request_status(
    body_info: RequestStatusUpdateSchema,
    role: Annotated[
        AccountRoleEnum, Path(description="Rol de la solicitud a actualizar")
    ],
    db: Annotated[Session, Depends(get_db)],
):
    return await RequestStatusController.update_request_status(
        data=body_info, role=role, db=db
    )


@router.get(
    "/user-info-by-token",
    summary="Obtener info de usuario por token",
    description="Endpoint para obtener la información de usuario asociada a un token de verificación. Usado en el flujo de confirmación de email.",
    response_model=UserInfoResponse,
)
async def confirm_email(token: UUID, db: Annotated[Session, Depends(get_db)]):
    return await GetUserInfoController.get_user_info(token=token, db=db)


@router.post(
    "/create-account",
    summary="Finalizar creación de cuenta",
    response_model=CreateAccountResponse,
)
async def create_account(
    body_info: CreateAccountSchema, db: Annotated[Session, Depends(get_db)]
):
    return await CreateAccountController.create_account(data=body_info, db=db)
