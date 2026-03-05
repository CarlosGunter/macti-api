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

            # Definición de transiciones de estado permitidas
            valid_transitions = {
                AccountStatusEnum.PENDING: {
                    AccountStatusEnum.APPROVED,
                    AccountStatusEnum.REJECTED,
                },
                AccountStatusEnum.APPROVED: {
                    AccountStatusEnum.REJECTED,
                    AccountStatusEnum.PENDING,
                },
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

            # --- PROCESAMIENTO SEGÚN EL NUEVO ESTADO ---
            if new_status == AccountStatusEnum.APPROVED:
                # Se eliminó la lógica de aprovisionamiento de Moodle de aquí.
                await ChangeStatusController._handle_approved(account_request, db)

            elif new_status == AccountStatusEnum.PENDING:
                ChangeStatusController._handle_pending(account_request)

            elif new_status == AccountStatusEnum.REJECTED:
                # El rechazo implica limpieza de tokens
                await ChangeStatusController._handle_rejected(
                    account_request, db, current_status
                )

            else:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "ESTADO_NO_COMPATIBLE",
                        "message": f"El estado {new_status} no puede ser procesado aquí.",
                    },
                )

            # Confirmación de cambios en la base de datos
            db.commit()
            db.refresh(account_request)

            return {
                "message": f"Estado actualizado a {new_status.value} correctamente."
            }

        except HTTPException as httpe:
            db.rollback()
            raise httpe

        except Exception as e:
            db.rollback()
            print(f"CRITICAL ERROR [change_status]: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error_code": "INTERNAL_SERVER_ERROR", "message": str(e)},
            ) from e

    @staticmethod
    async def _handle_approved(account_request: UserAccounts, db: Session):
        """Maneja la generación de tokens y envío de correos de bienvenida."""
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

    @staticmethod
    def _handle_pending(account_request: UserAccounts):
        """Revierte el estado a pendiente."""
        account_request.status = AccountStatusEnum.PENDING

    @staticmethod
    async def _handle_rejected(
        account_request: UserAccounts,
        db: Session,
        current_status: AccountStatusEnum,
    ):
        """Limpia los datos del usuario en BD."""
        db.query(VerificationToken).filter(
            VerificationToken.account_id == account_request.id
        ).delete(synchronize_session=False)
        if current_status == AccountStatusEnum.CREATED:
            # Eliminación de usuarios en Keycloak y Moodle por rechazo administrativo
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

            account_request.kc_id = None
            account_request.moodle_id = None
        account_request.status = AccountStatusEnum.REJECTED

    @classmethod
    def _generate_and_save_token(cls, account_id: int, db: Session):
        """Genera y persiste un token de verificación UUID4."""
        token = str(uuid4())
        ahora = datetime.now()
        expira = ahora + timedelta(days=7)

        try:
            validation = (
                db.query(VerificationToken)
                .filter(VerificationToken.account_id == account_id)
                .first()
            )

            if validation:
                validation.token = token
                validation.created_at = ahora
                validation.expires_at = expira
                validation.is_used = 0
            else:
                new_val = VerificationToken(
                    account_id=account_id,
                    token=token,
                    created_at=ahora,
                    expires_at=expira,
                    is_used=0,
                )
                db.add(new_val)

            return {"success": True, "token": token}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
