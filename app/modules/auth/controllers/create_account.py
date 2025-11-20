from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService

from ..models import AccountRequest, AccountStatusEnum, MCTValidacion
from ..schema import CreateAccountSchema


class CreateAccountController:
    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        """
        Crear o actualizar cuenta en Keycloak y Moodle usando user_id y new_password enviados desde el front.
        """
        account_request = (
            db.query(AccountRequest).filter(AccountRequest.id == data.user_id).first()
        )
        if not account_request:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NO_ENCONTRADO",
                    "message": "Solicitud no encontrada",
                },
            )

        if account_request.status != AccountStatusEnum.APPROVED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "STATUS_INVALIDO",
                    "message": "La solicitud debe estar aprobada antes de crear la cuenta",
                },
            )

        # Crear usuario en Keycloak
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
                    "message": f"Error creando usuario en Keycloak: {kc_result.get('error')}",
                },
            )

        account_request.kc_id = kc_result.get("user_id")

        # Crear usuario en Moodle (puedes agregar lógica similar si ya existe)
        moodle_result = await MoodleService.create_user(
            user_data={
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "course_id": account_request.course_id,
                "password": data.new_password,
            },
            institute=account_request.institute,
        )
        if not moodle_result.get("created"):
            raise HTTPException(
                status_code=502,
                detail={
                    "error_code": "MOODLE_ERROR",
                    "message": "Error creando usuario en Moodle",
                },
            )

        account_request.moodle_id = moodle_result.get("id")

        # Matricular usuario en el curso
        await MoodleService.enroll_user(
            user_id=moodle_result["id"],
            course_id=account_request.course_id,
            institute=account_request.institute,
        )

        # Actualizar estado de la solicitud
        account_request.status = AccountStatusEnum.CREATED
        token_record = (
            db.query(MCTValidacion)
            .filter(MCTValidacion.email == account_request.email)
            .first()
        )
        if token_record:
            db.delete(token_record)

        db.commit()
        db.refresh(account_request)
        return {
            "message": "Cuenta creada/actualizada exitosamente en Keycloak y Moodle",
        }
