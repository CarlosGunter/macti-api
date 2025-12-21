from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.shared.enums.enums import AccountRoleEnum  # <-- AGREGADO

from ....shared.models.users_model import AccountStatusEnum, UserAccounts
from ..schema import AccountRequestSchema


class RequestAccountController:
    @staticmethod
    def request_account(role: AccountRoleEnum, data: AccountRequestSchema, db: Session):
        existing_request = (
            db.query(UserAccounts)
            .filter(
                UserAccounts.email == data.email,
                UserAccounts.institute == data.institute,
            )
            .first()
        )

        # Si ya existe una solicitud con el mismo email e instituto, devolver error.
        if existing_request is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "EMAIL_EXISTENTE",
                    "message": "El correo ya tiene una solicitud.",
                },
            )

        try:
            db_account_request = UserAccounts(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                course_id=data.course_id,
                institute=data.institute,
                role=role,
                status=AccountStatusEnum.PENDING,
            )

            db.add(db_account_request)
            db.commit()
            db.refresh(db_account_request)

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
