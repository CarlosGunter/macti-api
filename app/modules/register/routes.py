# Módulo APIRouter de Autenticación y Registro - Proyecto MACTI
# Este archivo define las rutas para el flujo de solicitudes, aprobación y
# creación definitiva de cuentas de usuario.

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.register.controllers.get_user_info import GetUserInfoController
from app.modules.register.controllers.update_request_status import (
    RequestStatusController,
)
from app.shared.enums.role_enum import AccountRoleEnum

from .controllers.account_requests import AccountRequestsController
from .schemas import (
    AccountRequestResponse,
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
    body_info: StudentRequestSchema, db: Session = Depends(get_db)
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
    body_info: TeacherRequestSchema, db: Session = Depends(get_db)
):
    return await AccountRequestsController.request_account(
        role=AccountRoleEnum.DOCENTE, data=body_info, db=db
    )


# @router.get(
#     "/list-account-requests/students",
#     summary="Listar solicitudes de cuenta de alumnos por curso",
#     response_model=ListAccountsResponse,
# )
# async def list_accounts_requests(
#     course_id: int = Query(..., description="ID del curso en Moodle"),
#     institute: InstitutesEnum = Query(..., description="Instituto"),
#     status: AccountStatusEnum | None = Query(None),
#     db=Depends(get_db),
#     user_info=Depends(get_current_user),
# ):
#     return await ListAccountRequestsController.list_accounts_requests(
#         db=db,
#         course_id=course_id,
#         institute=institute,
#         status=status,
#         user_info=user_info,
#     )


# @router.get(
#     "/list-account-requests/teachers",
#     summary="Listar solicitudes de cuenta de docentes",
#     description="Endpoint para listar solicitudes de cuenta de docentes. Solo accesible para roles de gestión.",
#     response_model=ListAccountsResponse,
# )
# async def list_teacher_accounts_requests(
#     institute: InstitutesEnum = Query(..., description="Instituto"),
#     status: AccountStatusEnum | None = Query(None),
#     db=Depends(get_db),
#     user_info=Depends(get_current_user),
# ):
#     return await AccountRequestsTeacherController.list_teacher_accounts_requests(
#         institute=institute,
#         status=status,
#         user_info=user_info,
#         db=db,
#     )


@router.patch(
    "/update-request-status/{role}",
    summary="Cambiar estatus de una solicitud",
    description="Endpoint para que el administrador pueda aprobar/rechazar solicitudes de cuenta.",
    response_model=RequestStatusUpdateResponseSchema,
)
async def update_request_status(
    body_info: RequestStatusUpdateSchema,
    role: AccountRoleEnum = Path(..., description="Rol de la solicitud a actualizar"),
    db=Depends(get_db),
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
async def confirm_email(token: str, db: Session = Depends(get_db)):
    return await GetUserInfoController.get_user_info(token=token, db=db)


# @router.post(
#     "/create-account",
#     summary="Finalizar creación de cuenta",
#     response_model=CreateAccountResponse,
# )
# async def create_account(body_info: CreateAccountSchema, db=Depends(get_db)):
#     # El controlador es asíncrono (usa await)
#     return await CreateAccountController.create_account(data=body_info, db=db)
