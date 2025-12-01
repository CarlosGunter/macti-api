from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import AccountRequest, AccountStatusEnum
from ..schema import AccountRequestSchema


class RequestAccountController:
    @staticmethod
    def request_account(data: AccountRequestSchema, db: Session):
        existing_request = (
            db.query(AccountRequest)
            .filter(
                AccountRequest.email == data.email,
                AccountRequest.institute == data.institute,
            )
            .first()
        )

        if existing_request is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EMAIL_EXISTENTE",
                    "message": "El correo ya tiene una solicitud.",
                },
            )

        try:
            db_account_request = AccountRequest(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                course_id=data.course_id,
                institute=data.institute,
                role=data.role,
                status=AccountStatusEnum.PENDING,
            )

            db.add(db_account_request)
            db.commit()
            db.refresh(db_account_request)

            return {"message": "Solicitud de cuenta en proceso"}

        except SQLAlchemyError as err:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "DB_ERROR",
                    "message": "Error al registrar la solicitud",
                },
            ) from err

        except Exception as err:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ERROR_DESCONOCIDO",
                    "message": str(err),
                },
            ) from err  # no sé porque, pero si pongo ero from err pasa
