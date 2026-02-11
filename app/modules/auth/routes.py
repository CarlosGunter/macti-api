"""
Módulo APIRouter de Autenticación y Registro - Proyecto MACTI

Este router centraliza los endpoints del flujo de vida de una cuenta de usuario:
1. Solicitud inicial (Alumno/Docente).
2. Gestión administrativa (Listado y Cambio de estatus).
3. Validación de identidad (Tokens de correo).
4. Aprovisionamiento final (Keycloak y Moodle).
"""

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
    "/request-student-account",
    summary="Crear una solicitud de cuenta para ALUMNO",
    response_model=AccountRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_student_account(
    body_info: StudentRequestSchema, db: Session = Depends(get_db)
):
    """
    Endpoint para que un alumno solicite su acceso.
    Requiere vinculación inmediata a un course_id de Moodle.
    """
    return RequestAccountController.request_account(
        role=AccountRoleEnum.ALUMNO, data=body_info, db=db
    )


@router.post(
    "/request-teacher-account",
    summary="Crear una solicitud de cuenta para DOCENTE",
    response_model=AccountRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_teacher_account(
    body_info: TeacherRequestSchema, db: Session = Depends(get_db)
):
    """
    Endpoint para que un docente solicite acceso y, opcionalmente,
    la creación de un nuevo espacio académico (curso) en Moodle.
    """
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
    institute: InstitutesEnum = Query(
        ..., description="Instituto al que pertenece el curso"
    ),
    status: AccountStatusEnum | None = Query(
        None, description="Filtro opcional por estatus"
    ),
    db=Depends(get_db),
    user_info=Depends(get_current_user),
):
    """
    Endpoint administrativo que permite a los gestores visualizar solicitudes
    pendientes de aprobación, filtradas por curso y estatus.
    """
    return await ListAccountRequestsController.list_accounts_requests(
        db=db,
        course_id=course_id,
        institute=institute,
        status=status,
        user_info=user_info,
    )


@router.patch("/change-status", response_model=ConfirmAccountResponse)
async def confirm_account(body_info: ConfirmAccountSchema, db=Depends(get_db)):
    """
    Permite al administrador aprobar o rechazar una solicitud.
    Si se aprueba, dispara automáticamente la generación de tokens y envío de email.
    """
    return await ChangeStatusController.change_status(data=body_info, db=db)


@router.get("/user-info-by-token", response_model=UserInfoResponse)
def confirm_email(token: str = Query(...), db=Depends(get_db)):
    """
    Endpoint de validación de enlace.
    Resuelve la identidad del usuario a partir del token UUID enviado por correo.
    """
    return GetUserInfoController.get_user_info(token=token, db=db)


@router.post("/create-account", response_model=CreateAccountResponse)
async def create_account(body_info: CreateAccountSchema, db=Depends(get_db)):
    """
    Paso final del flujo.
    Aprovisiona al usuario en Keycloak y Moodle una vez que ha definido su contraseña.
    """
    return await CreateAccountController.create_account(data=body_info, db=db)
