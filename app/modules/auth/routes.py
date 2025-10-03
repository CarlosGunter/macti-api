from fastapi import APIRouter, Depends, Query
from .services.email_service import EmailService
from app.core.database import get_db
from .controllers import AuthController
from .schema import AccountRequestSchema, ConfirmAccountSchema, CreateAccountSchema, EmailValidationSchema
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/request-account",
    summary="Endpoint que se encarga de crear una solicitud de cuenta",
    description="La solicitud de cuenta se crea desde el perfil del estudiante (antes de inscribirse en un curso)"
)
async def request_account(body_info: AccountRequestSchema, db=Depends(get_db)):
    """Crea una nueva solicitud de cuenta para un estudiante."""
    return AuthController.request_account(data=body_info, db=db)


@router.get(
    "/list-accounts-requests",
    summary="Endpoint que se encarga de listar todas las solicitudes de cuenta de acurdo a un curso",
    description="Las solicitudes de cuenta se listan desde el perfil del profesor de un curso"
)
async def list_accounts_requests(
    course_id: int = Query(description="Filtra las solicitudes por ID de curso"),
    db=Depends(get_db)
):
    """Lista todas las solicitudes de cuenta filtradas por curso."""
    return AuthController.list_accounts_requests(db=db, course_id=course_id)


@router.patch(
    "/confirm-account",
    summary="Endpoint que se encarga de confirmar o rechazar una solicitud de cuenta",
    description="El profesor puede confirmar o rechazar una solicitud de cuenta desde su perfil"
)
async def confirm_account(body_info: ConfirmAccountSchema, db=Depends(get_db)):
    """Confirma o rechaza una solicitud de cuenta (profesor)."""
    return AuthController.confirm_account(data=body_info, db=db)


@router.post(
    "/create-account",
    summary="Endpoint que se encarga de crear una cuenta en Keycloak y Moodle",
    description="Este endpoint crea una cuenta en Keycloak y Moodle desde el perfil del administrador del sistema"
)
#Aquí se crea moodel por lo que entiendo
async def create_account(body_info: CreateAccountSchema, db=Depends(get_db)):
    """Crea una cuenta en Keycloak y Moodle (administrador)."""
    return await AuthController.create_account(data=body_info, db=db)

#Usas este para validar los correos?
@router.post("/validate-email", summary="Enviar correo de validación")
async def validate_email(body_info: EmailValidationSchema):
    result = EmailService.send_validation_email(to_email=body_info.email)
    return result

@router.get("/confirmacion", summary="Confirma un correo usando token")
async def confirm_email(token: str = Query(..., description="Token de validación enviado por email")):
    result = EmailService.validate_token(token)
    if not result.get("success"):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": result.get("error")
            }
        )
    
    return {
        "success": True,
        "message": "Correo confirmado correctamente",
        "data": result.get("data")
    }
