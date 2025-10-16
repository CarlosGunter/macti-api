from fastapi import APIRouter, Depends, Query
from app.core.database import get_db
from .controllers import AuthController
from .schema import AccountRequestSchema, ConfirmAccountSchema

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/request-account",
    summary="Crear una solicitud de cuenta"
)
async def request_account(body_info: AccountRequestSchema, db=Depends(get_db)):
    """Crea una nueva solicitud de cuenta para un estudiante."""
    return AuthController.request_account(data=body_info, db=db)

@router.get(
    "/list-accounts-requests",
    summary="Listar solicitudes de cuenta por curso"
)
async def list_accounts_requests(
    course_id: int = Query(description="Filtra por ID de curso"),
    db=Depends(get_db)
):
    return AuthController.list_accounts_requests(db=db, course_id=course_id)

@router.patch("/confirm-account", summary="Aprobar o rechazar solicitud y enviar correo")
async def confirm_account(body_info: ConfirmAccountSchema, db=Depends(get_db)):
    return await AuthController.confirm_account(data=body_info, db=db)

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