from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.auth.services.email_service import EmailService
from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService
from .models import AccountRequest
from .schema import AccountRequestSchema, ConfirmAccountSchema, CreateAccountSchema

class AuthController:
    @staticmethod
    def request_account(data: AccountRequestSchema, db: Session):
        """
        Crea una nueva solicitud de cuenta para un estudiante.
        Es usado en el endpoint /request-account
        """
        db_account_request = AccountRequest(
            name=data.name,
            last_name=data.last_name,
            email=data.email,
            course_id=data.course_id,
            status="pending"
        )
        db.add(db_account_request)
        db.commit()
        db.refresh(db_account_request)

        return {
            "success": True,
            "message": "Solicitud de cuenta en proceso"
        }

    @staticmethod
    def list_accounts_requests(
        db: Session,
        course_id: int
    ):
        """
        Obtiene todas las solicitudes de cuenta filtradas por curso
        Es usado en el endpoint /list-accounts-requests
        """
        account_requests = db.query(AccountRequest)\
            .filter(AccountRequest.course_id == course_id)\
            .all()
        
        return {
            "success": True,
            "message": "Listado de solicitudes de cuenta",
            "data": account_requests
        }

    @staticmethod
    def confirm_account(data: ConfirmAccountSchema, db: Session):
        request_id = data.id
        status = data.status
        
        if not request_id:
            raise HTTPException(status_code=400, detail="Request ID is required")

        query = db.query(AccountRequest).filter(AccountRequest.id == request_id)
        account_request = query.first()
        if not account_request:
            raise HTTPException(
                status_code=404,
                detail=f"Account request with ID {request_id} not found"
            )
        query.update({"status": status}) 
        db.commit()
        db.refresh(account_request)
        user_email = str(account_request.email)
        EmailService.send_validation_email(user_email)
        
        return {
            "success": True,
            "message": "Estado de la solicitud de cuenta actualizado con éxito"
        }

    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        user_id = data.id
        password = data.password

        if not all([user_id, password]):
            raise HTTPException(status_code=400, detail="User ID and password are required")

        account_request = db.query(AccountRequest).filter(AccountRequest.id == user_id).first()
        if not account_request:
            raise HTTPException(status_code=404, detail=f"Account request with ID {user_id} not found")
        if str(account_request.status) != "approved":
            raise HTTPException(status_code=400, detail="Account request must be approved before creating an account")

        keycloak_user_id = None
        moodle_user_id = None

        try:
            # Crear usuario en Keycloak
            kc_result = await KeycloakService.create_user({
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "password": password
            })
            if not kc_result.get("created"):
                raise HTTPException(status_code=500, detail=f"Failed to create user in Keycloak: {kc_result.get('error', 'Unknown error')}")
            
            keycloak_user_id = kc_result.get("user_id")
            account_request.kc_id = keycloak_user_id
            db.commit()
            db.refresh(account_request)

            # Crear usuario en Moodle
            moodle_result = await MoodleService.create_user({
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "course_id": account_request.course_id,
                "password": password
            })
            if not moodle_result.get("created"):
                raise Exception("Failed to create user in Moodle")

            moodle_user_id = moodle_result["id"]
            account_request.moodle_id = str(moodle_user_id)
            await MoodleService.enroll_user(user_id=moodle_user_id, course_id=account_request.course_id)
            db.commit()
            db.refresh(account_request)

            return {
                "success": True,
                "message": "Cuenta creada exitosamente en Keycloak y Moodle",
                "data": {"kc_id": keycloak_user_id, "moodle_id": moodle_user_id}
            }

        except Exception as e:
            # Si falla Moodle, eliminar usuario de Keycloak
            if keycloak_user_id:
                await KeycloakService.delete_user(keycloak_user_id)
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

