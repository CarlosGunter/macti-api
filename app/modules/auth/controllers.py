from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.auth.services import KeycloakService, MoodleService
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
            teacher=data.teacher,
            course_id=data.course_id,
            status="pending"
        )
        db.add(db_account_request)
        db.commit()
        db.refresh(db_account_request)

        return {"message": "Solicitud de cuenta en proceso", "account_request": db_account_request}

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
        
        return {"message": "Listado de solicitudes de cuenta", "account_requests": account_requests}

    @staticmethod
    def confirm_account(data: ConfirmAccountSchema, db: Session):
        """
        Confirma una solicitud de cuenta.
        Es usado en el endpoint /confirm-account
        """
        request_id = data.id
        status = data.status
        
        if not request_id:
            raise HTTPException(status_code=400, detail="Request ID is required")

        query = db.query(AccountRequest).filter(AccountRequest.id == request_id)
        if not query.first():
            raise HTTPException(
                status_code=404,
                detail=f"Account request with ID {request_id} not found"
            )
        
        # Update status
        query.update({"status": status}) 
        db.commit()
        
        # Refresh to get the updated record
        account_confirmed = db.query(AccountRequest).filter(AccountRequest.id == request_id).first()
        return {"message": "Estado de la solicitud de cuenta actualizado con éxito", "account_request": account_confirmed}
    
    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        """
        Crea una nueva cuenta de usuario en Keycloak y Moodle.
        Es usado en el endpoint /create-account
        """
        user_id = data.id
        password = data.password

        if not all([user_id, password]):
            raise HTTPException(status_code=400, detail="User ID and password are required")

        # Fetch the account request
        account_request = db.query(AccountRequest).filter(AccountRequest.id == user_id).first()
        if not account_request:
            raise HTTPException(
                status_code=404,
                detail=f"Account request with ID {user_id} not found"
            )

        if str(account_request.status) != "approved":
            raise HTTPException(
                status_code=400,
                detail="Account request must be approved before creating an account"
            )
        
        # Create the user in KC
        kc_result = await KeycloakService.create_user({
            "name": account_request.name,
            "last_name": account_request.last_name,
            "email": account_request.email,
            "password": password
        })
        if not kc_result.get("created"):
            raise HTTPException(
                status_code=500,
                detail="Failed to create user in Keycloak"
            )
        
        # Create the user in Moodle
        moodle_result = await MoodleService.create_user({
            "name": account_request.name,
            "last_name": account_request.last_name,
            "email": account_request.email,
            "course_id": account_request.course_id
        })
        if not moodle_result.get("created"):
            raise HTTPException(
                status_code=500,
                detail="Failed to create user in Moodle"
            )
        
        # Insert ids into the BD
        # account_request.status = "created"
        # account_request.keycloak_id = kc_result.get("id")
        # account_request.moodle_id = moodle_result.get("id")
        # db.commit()
        # db.refresh(account_request)
        
        return {
            "message": "Cuenta creada exitosamente en Keycloak y Moodle",
            # "keycloak_id": kc_result.get("id"),
            # "moodle_id": moodle_result.get("id")
        }
