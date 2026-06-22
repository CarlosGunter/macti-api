"""Rutas del módulo de registro y solicitudes de curso."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.db.database import get_db
from app.modules.register.controllers.authenticated_student_request import (
    AuthenticatedStudentRequestController,
)
from app.modules.register.controllers.authenticated_teacher_request import (
    AuthenticatedTeacherRequestController,
)
from app.modules.register.controllers.create_account import CreateAccountController
from app.modules.register.controllers.get_user_info import GetUserInfoController
from app.modules.register.controllers.list_account_requests import (
    ListAccountRequestsController,
)
from app.modules.register.controllers.list_account_requests_teacher import (
    AccountRequestsTeacherController,
)
from app.modules.register.controllers.update_request_status import (
    RequestStatusController,
)
from app.shared.dependecies.auth_current_user import CurrentUser, get_current_user
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.role_enum import AccountRoleEnum
from app.shared.enums.status_enum import RequestStatusEnum

from .controllers.account_requests import AccountRequestsController
from .schemas import (
    AccountRequestResponse,
    AuthenticatedStudentRequestSchema,
    AuthenticatedTeacherRequestSchema,
    CreateAccountResponse,
    CreateAccountSchema,
    ListAccountsResponse,
    ListTeacherAccountsResponse,
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
    "/request-account/student/authenticated",
    summary="Crear una solicitud de curso para ALUMNO autenticado",
    description="Endpoint para que un alumno autenticado solicite un curso usando su identidad actual.",
    response_model=AccountRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_authenticated_student_account(
    body_info: AuthenticatedStudentRequestSchema,
    db: Annotated[Session, Depends(get_db)],
    user_info: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, str]:
    """Registra una solicitud de curso usando la identidad autenticada del alumno."""
    return await AuthenticatedStudentRequestController.request_student_course(
        data=body_info,
        db=db,
        user_info=user_info,
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


@router.post(
    "/request-account/teacher/authenticated",
    summary="Crear una solicitud de nuevo curso para DOCENTE autenticado",
    description="Endpoint para que un docente autenticado solicite un nuevo curso usando su identidad actual.",
    response_model=AccountRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_authenticated_teacher_account(
    body_info: AuthenticatedTeacherRequestSchema,
    db: Annotated[Session, Depends(get_db)],
    user_info: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, str]:
    """Registra una solicitud de nuevo curso usando la identidad autenticada del docente."""
    return await AuthenticatedTeacherRequestController.request_teacher_course(
        data=body_info,
        db=db,
        user_info=user_info,
    )


@router.get(
    "/list-account-requests/students",
    summary="Listar solicitudes de cuenta de alumnos por curso",
    response_model=ListAccountsResponse,
)
async def list_accounts_requests(
    db: Annotated[Session, Depends(get_db)],
    user_info: Annotated[CurrentUser, Depends(get_current_user)],
    institute: InstitutesEnum = Query(..., description="Instituto"),
    course_id: int = Query(..., description="ID del curso en Moodle"),
    status: RequestStatusEnum | None = Query(
        None, description="Estatus de las solicitudes a filtrar"
    ),
):
    return await ListAccountRequestsController.list_accounts_requests(
        db=db,
        course_id=course_id,
        institute=institute,
        status=status,
        user_info=user_info,
    )


@router.get(
    "/list-account-requests/teachers",
    summary="Listar solicitudes de cuenta de docentes",
    description="Endpoint para listar solicitudes de cuenta de docentes. Solo accesible para roles de gestión.",
    response_model=ListTeacherAccountsResponse,
)
async def list_teacher_accounts_requests(
    db: Annotated[Session, Depends(get_db)],
    user_info: Annotated[CurrentUser, Depends(get_current_user)],
    institute: InstitutesEnum = Query(..., description="Instituto"),
    status: RequestStatusEnum | None = Query(
        None, description="Estatus de las solicitudes a filtrar"
    ),
):
    return await AccountRequestsTeacherController.list_teacher_accounts_requests(
        institute=institute,
        status=status,
        user_info=user_info,
        db=db,
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
    _: Annotated[CurrentUser, Depends(get_current_user)],
    institute: InstitutesEnum = Query(
        ..., description="Instituto al que pertenece la solicitud"
    ),
):
    return await RequestStatusController.update_request_status(
        data=body_info, role=role, db=db, institute=institute
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
