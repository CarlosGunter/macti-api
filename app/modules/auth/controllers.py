from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.modules.auth.services.email_service import EmailService
from .models import AccountRequest, AccountStatusEnum
from .schema import AccountRequestSchema, ConfirmAccountSchema, CreateAccountSchema
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
        """ moodle_result = await MoodleService.create_user({
            "name": account_request.name,
            "last_name": account_request.last_name,
            "email": account_request.email,
            "course_id": account_request.course_id,
            "password": data.new_password
        }) """
        """ if not moodle_result.get("created"):
            raise HTTPException(status_code=500, detail="Error creando usuario en Moodle") """

        # Matricular usuario en el curso
        """ await MoodleService.enroll_user(user_id=moodle_result["id"], course_id=account_request.course_id) """

        # Actualizar estado de la solicitud
        account_request.status = "created"
        db.commit()
        db.refresh(account_request)
        #"moodle_id": moodle_result.get("id")
        return {
            "success": True,
            "message": "Cuenta creada/actualizada exitosamente en Keycloak y Moodle",
            "keycloak_id": account_request.kc_id
            
        }
