from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.modules.auth.services.email_service import EmailService
from app.modules.auth.services.kc_service import KeycloakService
from app.modules.auth.services.moodle_service import MoodleService
from .models import AccountRequest
from .schema import AccountRequestSchema, ConfirmAccountSchema, CreateAccountSchema
from app.modules.auth.models import AccountStatusEnum


class AuthController:

    @staticmethod
    def request_account(data: AccountRequestSchema, db: Session):
        """
        Crea una nueva solicitud de cuenta para un estudiante.
        Usado en el endpoint /request-account
        """
        existing_request = db.query(AccountRequest).filter(
            AccountRequest.email == data.email
        ).first()

        if existing_request:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EMAIL_EXISTS",
                    "message": "El correo ya cuenta con una solicitud registrada."
                }
            )

        try:
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
            return {"success": True, "message": "Solicitud de cuenta en proceso"}

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error SQL al crear solicitud: {e}")
            raise HTTPException(status_code=500, detail="Error al registrar la solicitud de cuenta")
        except Exception as e:
            db.rollback()
            print(f"Error inesperado: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def list_accounts_requests(db: Session, course_id: int):
        """
        Obtiene todas las solicitudes de cuenta filtradas por curso.
        Usado en el endpoint /list-accounts-requests
        """
        try:
            account_requests = (
                db.query(AccountRequest)
                .filter(AccountRequest.course_id == course_id)
                .all()
            )
            return {
                "success": True,
                "message": "Listado de solicitudes de cuenta",
                "data": account_requests
            }
        except SQLAlchemyError as e:
            print(f"Error SQL al listar solicitudes: {e}")
            raise HTTPException(status_code=500, detail="Error al obtener solicitudes de cuenta")
        except Exception as e:
            print(f"Error inesperado al listar solicitudes: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def confirm_account(data: ConfirmAccountSchema, db: Session):
        """
        Actualiza el estado de una solicitud de cuenta.
        Si la solicitud es aprobada, envía correo de validación.
        """
        request_id = data.id
        status = data.status

        if not request_id:
            raise HTTPException(status_code=400, detail="Request ID is required")

        try:
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

            # Solo enviar correo si fue aprobada
            if status.lower() == "approved":
                user_email = str(account_request.email)
                email_result = EmailService.send_validation_email(user_email)
                if isinstance(email_result, dict) and "error" in email_result:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error al enviar correo de validación: {email_result['error']}"
                    )

            return {
                "success": True,
                "message": "Estado de la solicitud actualizado con éxito"
            }

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error SQL al confirmar solicitud: {e}")
            raise HTTPException(status_code=500, detail="Error al actualizar la solicitud")
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            print(f"Error inesperado al confirmar solicitud: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def create_account(data: CreateAccountSchema, db: Session):
        """
        Crea cuenta de usuario en Keycloak y Moodle, vinculada a la solicitud.
        """
        user_id = data.id
        password = data.password
        keycloak_user_id = None
        moodle_user_id = None

        if not all([user_id, password]):
            raise HTTPException(status_code=400, detail="User ID and password are required")

        try:
            account_request = db.query(AccountRequest).filter(AccountRequest.id == user_id).first()

            if not account_request:
                raise HTTPException(status_code=404, detail=f"Account request with ID {user_id} not found")

            if account_request.status.value != AccountStatusEnum.approved.value:
                raise HTTPException(status_code=400, detail="Account request must be approved before creating an account")

            # Crear usuario en Keycloak
            kc_result = await KeycloakService.create_user({
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "password": password
            })
            keycloak_user_id = kc_result.get("user_id")

            if not kc_result.get("created") or keycloak_user_id is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create user in Keycloak: {kc_result.get('error', 'Unknown error')}"
                )

            account_request.kc_id = keycloak_user_id

            # Crear usuario en Moodle
            moodle_result = await MoodleService.create_user({
                "name": account_request.name,
                "last_name": account_request.last_name,
                "email": account_request.email,
                "course_id": account_request.course_id,
                "password": password
            })
            
            if not moodle_result.get("created") or moodle_user_id is None:
                raise Exception("Failed to create user in Moodle")

            moodle_user_id = moodle_result["id"]
            account_request.moodle_id = moodle_user_id

            # Inscribir al usuario en el curso
            await MoodleService.enroll_user(
                user_id=moodle_user_id,
                course_id=account_request.course_id
            )

            db.commit()
            db.refresh(account_request)

            return {
                "success": True,
                "message": "Cuenta creada exitosamente en Keycloak y Moodle"
            }

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error SQL durante creación de cuenta: {e}")
            raise HTTPException(status_code=500, detail="Error de base de datos durante creación de cuenta")
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            # Si falla Moodle, eliminar usuario en Keycloak
            if keycloak_user_id:
                print("Eliminando usuario de Keycloak por rollback")
                await KeycloakService.delete_user(keycloak_user_id)
            db.rollback()
            print(f"Error inesperado en creación de cuenta: {e}")
            raise HTTPException(status_code=500, detail=str(e))
