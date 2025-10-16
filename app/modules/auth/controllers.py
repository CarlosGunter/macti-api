from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.modules.auth.services.email_service import EmailService
from .models import AccountRequest, AccountStatusEnum
from .schema import AccountRequestSchema, ConfirmAccountSchema
from app.modules.auth.services.kc_service import KeycloakService

class AuthController:
    @staticmethod
    def request_account(data: AccountRequestSchema, db: Session):
        existing_request = db.query(AccountRequest).filter(
            AccountRequest.email == data.email
        ).first()
        if existing_request:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "EMAIL_EXISTS", "message": "El correo ya tiene una solicitud."}
            )
        try:
            db_account_request = AccountRequest(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                course_id=data.course_id,
                status=AccountStatusEnum.pending
            )
            db.add(db_account_request)
            db.commit()
            db.refresh(db_account_request)
            return {"success": True, "message": "Solicitud de cuenta en proceso"}
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error al registrar la solicitud")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def list_accounts_requests(db: Session, course_id: int):
        try:
            requests = db.query(AccountRequest).filter(
                AccountRequest.course_id == course_id
            ).all()
            return {"success": True, "data": requests}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail="Error al obtener solicitudes")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def confirm_account(data: ConfirmAccountSchema, db: Session):
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

                token_data = EmailService.generate_and_save_token(user_email)
                if not token_data.get("success"):
                    # Si falla, eliminamos Keycloak
                    await KeycloakService.delete_user(account_request.kc_id)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error al generar token: {token_data.get('error')}"
                    )
                token = token_data.get("token")
                confirm_link = f"http://localhost:3000/registro/confirmacion?token={token}"
                email_result = EmailService.send_validation_email(user_email)
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

    #Esta es la que valida y hace el cambio de pass
    @staticmethod
    async def complete_account(token: str, new_password: str, db: Session):
        from app.modules.auth.models import MCT_Validacion, AccountRequest
        validation = db.query(MCT_Validacion).filter(
            MCT_Validacion.token == token
        ).first()

        if not validation:
            raise HTTPException(status_code=400, detail="Token inválido o ya usado")
        account_request = db.query(AccountRequest).filter(
            AccountRequest.email == validation.email
        ).first()

        if not account_request or not account_request.kc_id:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        result = await KeycloakService.update_user_password(account_request.kc_id, new_password)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=f"Error actualizando contraseña: {result.get('error')}")
        account_request.status = "created"
        db.delete(validation)
        db.commit()
        db.refresh(account_request)

        return {"success": True, "message": "Cuenta activada, contraseña actualizada y token eliminado"}

