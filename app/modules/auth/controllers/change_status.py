# Módulo ChangeStatusController - Gestión del Ciclo de Vida de Solicitudes
# Este controlador maneja la transición de estados de las solicitudes de cuenta.
# Su función principal es validar la aprobación de una cuenta y coordinar el envío de correos.

from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.email_service import EmailService
from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService
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
    async def change_status(data: ConfirmAccountSchema, db: Session):
        """
        Cambia el estatus de una solicitud de cuenta específica.

        Si el estatus es 'APPROVED', inicia el flujo de verificación:
        1. Genera un token UUID único.
        2. Guarda el token en la base de datos relacionado con la cuenta.
        3. Envía un correo electrónico al usuario con el enlace de validación.
        """
        request_id = data.id
        new_status = data.status

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

            current_status = account_request.status

            if new_status == current_status:
                return {"message": f"Sin cambios: el estado ya es {new_status.value}"}

            # Transiciones permitidas
            valid_transitions = {
                AccountStatusEnum.PENDING: {
                    AccountStatusEnum.APPROVED,
                    AccountStatusEnum.REJECTED,
                },
                AccountStatusEnum.APPROVED: {AccountStatusEnum.REJECTED},
                AccountStatusEnum.REJECTED: {
                    AccountStatusEnum.PENDING,
                    AccountStatusEnum.APPROVED,
                },
                AccountStatusEnum.CREATED: {AccountStatusEnum.REJECTED},
            }

            if new_status not in valid_transitions.get(current_status, set()):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error_code": "TRANSICION_INVALIDA",
                        "message": f"No se puede pasar de {current_status.value} a {new_status.value}",
                    },
                )

            # Acciones según estado destino
            if new_status == AccountStatusEnum.APPROVED:
                ChangeStatusController._handle_approved(account_request, db)

            elif new_status == AccountStatusEnum.PENDING:
                ChangeStatusController._handle_pending(account_request)

            elif new_status == AccountStatusEnum.REJECTED:
                await ChangeStatusController._handle_rejected(
                    account_request, db, current_status
                )

            else:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "ESTADO_DESTINO_NO_SOPORTADO",
                        "message": f"Estado destino no soportado: {new_status}",
                    },
                )

            db.commit()
            db.refresh(account_request)

            if new_status == AccountStatusEnum.APPROVED:
                return {
                    "message": f"Solicitud aprobada. Correo de validación enviado a {account_request.email}"
                }

            return {"message": f"Estado actualizado correctamente a {new_status.value}"}

        except HTTPException as httpe:
            db.rollback()
            raise httpe

        except Exception as e:
            db.rollback()
            print(f"Error en change_status: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error_code": "ERROR_DESCONOCIDO", "message": str(e)},
            ) from e

    @staticmethod
    def _handle_approved(account_request: UserAccounts, db: Session):
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

        email_result = EmailService.send_validation_email(
            to_email=account_request.email,
            token=token,
        )

        if not email_result.get("success"):
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "EMAIL_ERROR",
                    "message": "Falló el envío del correo de validación.",
                },
            )

        account_request.status = AccountStatusEnum.APPROVED
        return {"token": token}

    @staticmethod
    def _handle_pending(account_request: UserAccounts):
        account_request.status = AccountStatusEnum.PENDING

    @staticmethod
    async def _handle_rejected(
        account_request: UserAccounts,
        db: Session,
        current_status: AccountStatusEnum,
    ):
        db.query(VerificationToken).filter(
            VerificationToken.account_id == account_request.id
        ).delete(synchronize_session=False)

        if current_status == AccountStatusEnum.CREATED:
            if getattr(account_request, "kc_id", None):
                await KeycloakService.delete_user(
                    user_id=str(account_request.kc_id),
                    institute=account_request.institute,
                )

            if getattr(account_request, "moodle_id", None):
                await MoodleService.delete_user(
                    user_id=str(account_request.moodle_id),
                    institute=account_request.institute,
                )

            if hasattr(account_request, "kc_id"):
                account_request.kc_id = None
            if hasattr(account_request, "moodle_id"):
                account_request.moodle_id = None

        account_request.status = AccountStatusEnum.REJECTED

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

            return {"success": True, "token": token}

        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Error en BD: {e}"}
