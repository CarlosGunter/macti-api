from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.auth.services.email_service import EmailService
from ..models import AccountRequest, AccountStatusEnum
from ..schema import ConfirmAccountSchema
from app.modules.auth.services.kc_service import KeycloakService

class ChangeStatusController:
    @staticmethod
    async def change_status(data: ConfirmAccountSchema, db: Session):
        request_id = data.id
        status = data.status

        try:
            account_request = db.query(AccountRequest).filter(AccountRequest.id == request_id).first()
            if not account_request:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "NO_ENCONTRADO",
                        "message": "Solicitud de cuenta no encontrada"
                    },
                )

            account_request.status = status
            db.commit()
            db.refresh(account_request)

            if status == AccountStatusEnum.approved:
                user_email = account_request.email
                user_firstname = account_request.name
                user_lastname = account_request.last_name
                keycloak_result = await KeycloakService.create_user({
                    "email": user_email,
                    "name": user_firstname,
                    "last_name": user_lastname,
                    "password": "temporal123"
                })
                if not keycloak_result.get("created"):
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "KC_ERROR",
                            "message": "Error al crear usuario en Keycloak"
                        }
                    )

                account_request.kc_id = keycloak_result.get("user_id")

                token_data = EmailService.generate_and_save_token(user_email)
                if not token_data.get("success"):
                    # Si falla, eliminamos Keycloak
                    await KeycloakService.delete_user(account_request.kc_id)
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "TOKEN_ERROR",
                            "message": f"Error al generar token: {token_data.get('error')}"
                        }
                    )
                token = token_data.get("token")
                confirm_link = f"http://localhost:3000/registro/confirmacion?token={token}"
                email_result = EmailService.send_validation_email(user_email)
                if not email_result.get("success"):
                    print(f"ALERTA: Falló el envío de correo para {user_email}: {email_result.get('error')}")
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "EMAIL_ERROR",
                            "message": "Cuenta creada, pero falló el envío del correo de validación."
                        }
                    )
                
                db.commit()
                db.refresh(account_request)

                return {
                    "message": f"Cuenta creada en Keycloak y correo de validación enviado a {user_email}"
                }

        # Re-lanzamos las HTTPException controladas para que lleguen tal cual al endpoint
        except HTTPException as httpe:
            db.rollback()
            raise httpe

        # Solo aquí atrapamos excepciones inesperadas y las convertimos a 500
        except Exception as e:
            db.rollback()
            print(f"Error en confirm_account: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "ERROR_DESCONOCIDO",
                    "message": str(e)
                }
            )
