from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.auth.services.moodle_service import MoodleService
from ..models import AccountRequest, AccountStatusEnum
from ..schema import CreateAccountSchema
from app.modules.auth.services.kc_service import KeycloakService

class CreateAccountController:
    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        """
        Crear o actualizar cuenta en Keycloak y Moodle usando user_id y new_password enviados desde el front.
        """
        account_request = db.query(AccountRequest).filter(AccountRequest.id == data.user_id).first()
        if not account_request:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        if account_request.status != AccountStatusEnum.approved:
            raise HTTPException(status_code=400, detail="La solicitud debe estar aprobada antes de crear la cuenta")

        # Revisar si ya tiene kc_id (usuario existente en Keycloak)
        if str(account_request.kc_id):
            # Actualizar contraseña
            kc_result = await KeycloakService.update_user_password(account_request.kc_id, data.new_password)
            if not kc_result.get("success"):
                raise HTTPException(status_code=500, detail=f"Error actualizando contraseña en Keycloak: {kc_result.get('error')}")
        else:
            # Crear usuario en Keycloak
            kc_result = await KeycloakService.create_user({
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "password": data.new_password
            })
            if not kc_result.get("created"):
                raise HTTPException(status_code=500, detail=f"Error creando usuario en Keycloak: {kc_result.get('error')}")
            account_request.kc_id = kc_result.get("user_id")

        # Crear usuario en Moodle (puedes agregar lógica similar si ya existe)
        moodle_result = await MoodleService.create_user({
            "name": account_request.name,
            "last_name": account_request.last_name,
            "email": account_request.email,
            "course_id": account_request.course_id,
            "password": data.new_password
        })
        if not moodle_result.get("created"):
            raise HTTPException(status_code=500, detail="Error creando usuario en Moodle")
        
        account_request.moodle_id = moodle_result.get("id")
        
        # Matricular usuario en el curso
        await MoodleService.enroll_user(
            user_id=moodle_result["id"],
            course_id=account_request.course_id
        ) 
        
        # Actualizar estado de la solicitud
        account_request.status = AccountStatusEnum.created
        token_record = db.query(MCT_Validacion).filter(MCT_Validacion.email == account_request.email).first()
        if token_record:
             db.delete(token_record)
        db.commit()
        db.refresh(account_request)
        return {
            "success": True,
            "message": "Cuenta creada/actualizada exitosamente en Keycloak y Moodle",
            "keycloak_id": account_request.kc_id
            
        }