from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.email_service import EmailService
from app.modules.auth.services.kc_service import KeycloakService

from ..models import AccountRequest, AccountStatusEnum, MCTValidacion
from ..schema import ConfirmAccountSchema


class ChangeStatusController:
    @staticmethod
    async def change_status(data: ConfirmAccountSchema, db: Session):
        request_id = data.id
        status = data.status

        try:
            account_request = (
                db.query(AccountRequest).filter(AccountRequest.id == request_id).first()
            )
            if not account_request:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "NO_ENCONTRADO",
                        "message": "Solicitud de cuenta no encontrada",
                    },
                )

            if status == AccountStatusEnum.APPROVED:
                user_email = account_request.email

                token_data = ChangeStatusController._generate_and_save_token(
                    account_request.id, db
                )
                token = token_data.get("token")

                if not token:
                    # Si falla, eliminamos Keycloak
                    await KeycloakService.delete_user(
                        user_id=str(account_request.kc_id),
                        institute=account_request.institute,
                    )
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "TOKEN_ERROR",
                            "message": f"Error al generar token: {token_data.get('error')}",
                        },
                    )

                email_result = EmailService.send_validation_email(
                    to_email=user_email, token=token
                )
                if not email_result.get("success"):
                    print(
                        f"ALERTA: Falló el envío de correo para {user_email}: {email_result.get('error')}"
                    )
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "EMAIL_ERROR",
                            "message": "Cuenta creada, pero falló el envío del correo de validación.",
                        },
                    )

                account_request.status = status
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
                detail={"error_code": "ERROR_DESCONOCIDO", "message": str(e)},
            ) from e

    @classmethod
    def _generate_and_save_token(cls, account_id: int, db: Session):
        token = str(uuid4())
        fecha_solicitud = datetime.now()
        fecha_expiracion = fecha_solicitud + timedelta(days=7)

        try:
            # Get the account to retrieve email
            account = (
                db.query(AccountRequest).filter(AccountRequest.id == account_id).first()
            )
            if not account:
                return {"success": False, "error": "Account not found"}

            email = account.email

            # Query MCTValidacion by account_id
            validation = (
                db.query(MCTValidacion)
                .filter(MCTValidacion.account_id == account_id)
                .first()
            )

            if validation:
                # Update existing record
                validation.token = token
                validation.fecha_solicitud = fecha_solicitud
                validation.fecha_expiracion = fecha_expiracion
            else:
                # Create new record
                new_validation = MCTValidacion(
                    account_id=account_id,
                    email=email,
                    token=token,
                    fecha_solicitud=fecha_solicitud,
                    fecha_expiracion=fecha_expiracion,
                    bandera=0,
                )
                db.add(new_validation)

            db.commit()
            return {"success": True, "token": token}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error en BD: {e}"}
