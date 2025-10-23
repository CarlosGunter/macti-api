from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.auth.services.email_service import EmailService
from ..models import AccountRequest
from ..schema import ConfirmAccountSchema
from app.modules.auth.services.kc_service import KeycloakService

class ChangeStatusController:
    @staticmethod
    async def change_status(data: ConfirmAccountSchema, db: Session):
        request_id = data.id
        status = data.status.lower()

        if not request_id:
            raise HTTPException(status_code=400, detail="Request ID is required")

        try:
            account_request = db.query(AccountRequest).filter(AccountRequest.id == request_id).first()
            if not account_request:
                raise HTTPException(status_code=404, detail=f"Account request with ID {request_id} not found")

            account_request.status = status
            db.commit()
            db.refresh(account_request)

            if status == "approved":
                user_email = account_request.email
                user_firstname = account_request.name
                user_lastname = account_request.last_name
                institute = account_request.institute  

                # Crear usuario en Keycloak
                keycloak_result = await KeycloakService.create_user({
                    "email": user_email,
                    "name": user_firstname,
                    "last_name": user_lastname,
                    "password": "temporal123"
                })

                if not keycloak_result.get("created"):
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error creando usuario en Keycloak: {keycloak_result.get('error')}"
                    )

                account_request.kc_id = keycloak_result.get("user_id")

                # Generar token y enviar correo de validación
                token_data = EmailService.generate_and_save_token(user_email, institute)
                if not token_data.get("success"):
                    # Si falla, eliminamos Keycloak
                    await KeycloakService.delete_user(account_request.kc_id)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error al generar token: {token_data.get('error')}"
                    )

                token = token_data.get("token")
                email_result = EmailService.send_validation_email(
                    to_email=user_email,
                    institute=institute
                )

                if not email_result.get("success"):
                    print(f"ALERTA: Falló el envío de correo para {user_email}: {email_result.get('error')}")
                    return {
                        "success": False,
                        "message": "Cuenta creada, pero falló el envío del correo de validación.",
                        "token_sent": token
                    }

                db.commit()
                db.refresh(account_request)

                return {
                    "success": True,
                    "message": f"Cuenta creada en Keycloak y correo de validación enviado a {user_email}",
                    "token_sent": token
                }

        except Exception as e:
            db.rollback()
            print(f"Error en confirm_account: {e}")
            raise HTTPException(status_code=500, detail=str(e))
