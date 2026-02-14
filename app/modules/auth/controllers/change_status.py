# Módulo ChangeStatusController - Gestión del Ciclo de Vida de Solicitudes
# Este controlador maneja la transición de estados de las solicitudes de cuenta.
# Su función principal es validar la aprobación de una cuenta y coordinar el envío de correos.

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.email_service import EmailService
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.users_model import UserAccounts
from app.shared.models.verification_tokens_model import VerificationToken

from ..schema import ConfirmAccountSchema


class ChangeStatusController:
    """
    Controlador encargado de actualizar el estado de las solicitudes de cuenta
    y gestionar la lógica de negocio asociada a la aprobación.
    """

    @staticmethod
    def change_status(data: ConfirmAccountSchema, db: Session):
        """
        Cambia el estatus de una solicitud de cuenta específica.

        Si el estatus es 'APPROVED', inicia el flujo de verificación:
        1. Genera un token UUID único.
        2. Guarda el token en la base de datos relacionado con la cuenta.
        3. Envía un correo electrónico al usuario con el enlace de validación.
        """
        request_id = data.id
        status = data.status

        try:
            # Búsqueda de la solicitud por ID único
            account_request = (
                db.query(UserAccounts).filter(UserAccounts.id == request_id).first()
            )

            if not account_request:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "NO_ENCONTRADO",
                        "message": "Solicitud de cuenta no encontrada",
                    },
                )

            # Lógica específica cuando el Administrador aprueba la solicitud
            if status == AccountStatusEnum.APPROVED:
                user_email = account_request.email

                # Generación de token de seguridad
                token_data = ChangeStatusController._generate_and_save_token(
                    account_request.id, db
                )
                token = token_data.get("token")

                if not token:
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "TOKEN_ERROR",
                            "message": f"Error al generar token: {token_data.get('error')}",
                        },
                    )

                # Envío de correo electrónico vía SMTP
                email_result = EmailService.send_validation_email(
                    to_email=user_email, token=token
                )

                if not email_result.get("success"):
                    # Si el correo falla, se lanza una excepción para evitar que el
                    # estatus cambie a APPROVED sin que el usuario reciba su acceso.
                    print(
                        f"ALERTA: Falló el envío de correo para {user_email}: {email_result.get('error')}"
                    )
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error_code": "EMAIL_ERROR",
                            "message": "Cuenta aprobada, pero falló el envío del correo de validación.",
                        },
                    )

                # Persistencia del cambio de estado
                account_request.status = status
                db.commit()
                db.refresh(account_request)

                return {
                    "message": f"Solicitud aprobada y correo de validación enviado a {user_email}"
                }

        except HTTPException as httpe:
            db.rollback()
            raise httpe

        except Exception as e:
            db.rollback()
            print(f"Error en confirm_account: {e}")
            raise HTTPException(
                status_code=400,
                detail={"error_code": "ERROR_DESCONOCIDO", "message": str(e)},
            ) from e

    @classmethod
    def _generate_and_save_token(cls, account_id: int, db: Session):
        """
        Método interno para la gestión de tokens de verificación.

        Genera un identificador único (UUID4) con una vigencia de 7 días.
        Si ya existe un token previo para la cuenta, lo actualiza (UPSERT).
        """
        token = str(uuid4())
        fecha_solicitud = datetime.now()
        fecha_expiracion = fecha_solicitud + timedelta(days=7)

        try:
            account = (
                db.query(UserAccounts).filter(UserAccounts.id == account_id).first()
            )
            if not account:
                return {"success": False, "error": "Account not found"}

            # Verificación de existencia previa de token
            validation = (
                db.query(VerificationToken)
                .filter(VerificationToken.account_id == account_id)
                .first()
            )

            if validation:
                # Actualización de token existente (Renovación)
                validation.token = token
                validation.created_at = fecha_solicitud
                validation.expires_at = fecha_expiracion
                validation.is_used = 0
            else:
                # Creación de nuevo registro de verificación
                new_validation = VerificationToken(
                    account_id=account_id,
                    token=token,
                    created_at=fecha_solicitud,
                    expires_at=fecha_expiracion,
                    is_used=0,
                )
                db.add(new_validation)

            db.commit()
            return {"success": True, "token": token}

        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error en BD: {e}"}
