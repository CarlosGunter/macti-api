from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.modules.auth.enums import AccountRoleEnum
from app.modules.auth.models import AccountRequest
from app.modules.auth.schema import AccountRequestSchema


class RequestAccountController:
    @staticmethod
    def request_account(role: AccountRoleEnum, data: AccountRequestSchema, db):
        try:
            new_request = AccountRequest(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                course_id=data.course_id,
                role=role,
                institute=data.institute,
            )

            db.add(new_request)
            db.commit()
            db.refresh(new_request)
            return {"message": "Solicitud de cuenta en proceso"}

        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error al registrar la solicitud",
                },
            ) from None

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ERROR_DESCONOCIDO",
                    "message": "Ocurrió un error inesperado",
                },
            ) from None
