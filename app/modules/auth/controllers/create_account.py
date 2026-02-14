from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService
from app.shared.enums.status_enum import AccountStatusEnum
from app.shared.models.users_model import UserAccounts
from app.shared.models.verification_tokens_model import VerificationToken

from ..schema import CreateAccountSchema


class CreateAccountController:
    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        # 1. Validación de la solicitud
        account_request = (
            db.query(UserAccounts).filter(UserAccounts.id == data.user_id).first()
        )

        if not account_request:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NO_ENCONTRADO",
                    "message": "Solicitud no encontrada",
                },
            )

        # Validación de estatus
        if account_request.status != AccountStatusEnum.APPROVED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "STATUS_INVALIDO",
                    "message": "La solicitud debe estar aprobada",
                },
            )

        # 2. Keycloak (Aprovisionamiento)
        kc_result = await KeycloakService.create_user(
            {
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "password": data.new_password,
            },
            institute=account_request.institute,
        )

        if not kc_result.get("created"):
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "KC_ERROR",
                    "message": f"Error en Keycloak: {kc_result.get('error')}",
                },
            )

        # Convertimos a UUID de forma segura
        kc_user_id = kc_result.get("user_id")
        if kc_user_id:
            account_request.kc_id = UUID(str(kc_user_id))

        # 3. Moodle (Aprovisionamiento)
        current_course_id = account_request.course_id
        if current_course_id is None:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "DATA_INCOMPLETE", "message": "ID de curso nulo"},
            )
        try:
            moodle_result = await MoodleService.create_user(
                user_data={
                    "name": account_request.name,
                    "last_name": account_request.last_name,
                    "email": account_request.email,
                    "course_id": current_course_id,
                },
                institute=account_request.institute,
            )
        except Exception as e:
            if account_request.kc_id:
                await KeycloakService.delete_user(
                    user_id=str(account_request.kc_id),
                    institute=account_request.institute,
                )
            print(f"ERROR CRÍTICO EN MOODLE: {str(e)}")  # Esto saldrá en tu consola
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "MOODLE_CONNECTION_ERROR",
                    "message": f"No se pudo conectar con Moodle: {str(e)}",
                },
            ) from e
        if not moodle_result.get("created"):
            if account_request.kc_id:
                await KeycloakService.delete_user(
                    user_id=str(account_request.kc_id),
                    institute=account_request.institute,
                )
            raise HTTPException(
                status_code=502,
                detail={"error_code": "MOODLE_ERROR", "message": "Error en Moodle"},
            )

        account_request.moodle_id = moodle_result.get("id")
        m_user_id = account_request.moodle_id

        # 4. Inscripción Automática
        if m_user_id is not None:
            await MoodleService.enroll_user(
                user_id=m_user_id,
                course_id=current_course_id,
                institute=account_request.institute,
            )

        # 5. Finalización
        account_request.status = AccountStatusEnum.CREATED

        token_record = (
            db.query(VerificationToken)
            .filter(VerificationToken.account_id == account_request.id)
            .first()
        )
        if token_record:
            db.delete(token_record)

        db.commit()
        db.refresh(account_request)

        return {
            "message": "Cuenta creada exitosamente",
            "kc_id": str(account_request.kc_id),
            "moodle_id": account_request.moodle_id,
        }
