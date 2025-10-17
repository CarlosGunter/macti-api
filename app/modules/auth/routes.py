from fastapi import APIRouter, Depends, Query
from app.core.database import get_db
from .controllers import AuthController
from .schema import AccountRequestSchema, ConfirmAccountSchema, CreateAccountSchema
from app.modules.auth.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["auth"])

# Crear solicitud de cuenta
@router.post("/request-account", summary="Crear una solicitud de cuenta")
async def request_account(body_info: AccountRequestSchema, db=Depends(get_db)):
    result = AuthController.request_account(data=body_info, db=db)
    return {"success": True, "data": result}

# Listar solicitudes por curso
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

# Aprobar o rechazar solicitud y enviar correo
@router.patch("/confirm-account", summary="Aprobar o rechazar solicitud y enviar correo")
async def confirm_account(body_info: ConfirmAccountSchema, db=Depends(get_db)):
    result = await AuthController.confirm_account(data=body_info, db=db)
    return {"success": True, "data": result}

# Crear cuenta en Keycloak y Moodle 
@router.post("/create-account", summary="Crear cuenta en Keycloak y Moodle")
async def create_account(body_info: CreateAccountSchema, db=Depends(get_db)):
    result = await AuthController.create_account(data=body_info, db=db)
    return {"success": True, "data": result}

# Confirmar datos token
@router.get("/confirmacion", summary="Confirmar email con token")
def confirm_email(token: str):
    result = EmailService.validate_token(token)

    if result["success"]:
        return {
            "success": True,
            "message": result["message"],
            "data": result.get("data")
        }
    else:
        return {
            "success": False,
            "message": result.get("message", "Error desconocido")
        }
