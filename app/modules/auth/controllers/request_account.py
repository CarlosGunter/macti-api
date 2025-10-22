from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from ..models import AccountRequest, AccountStatusEnum
from ..schema import AccountRequestSchema

class RequestAccountController:
    @staticmethod
    def request_account(data: AccountRequestSchema, db: Session):
        
        existing_request = db.query(AccountRequest).filter(
            AccountRequest.email == data.email
        ).first()
        if existing_request:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EMAIL_EXISTENTE",
                    "message": "El correo ya tiene una solicitud."
                }
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
            
            return {
                "message": "Solicitud de cuenta en proceso"
            }

        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error al registrar la solicitud"
                }
            )
        
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ERROR_DESCONOCIDO",
                    "message": str(e)
                }
            )