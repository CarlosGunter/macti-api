from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.shared.enums.role_enum import AccountRoleEnum

from ....shared.models.users_model import AccountStatusEnum, UserAccounts
from ..schema import StudentRequestSchema, TeacherRequestSchema


class RequestAccountController:
    @staticmethod
    def request_account(
        role: AccountRoleEnum,
        data: StudentRequestSchema | TeacherRequestSchema,
        db: Session,
    ):
        existing_request = (
            db.query(UserAccounts)
            .filter(
                UserAccounts.email == data.email,
                UserAccounts.institute == data.institute,
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
            db_account_request = UserAccounts(
                name=data.name,
                last_name=data.last_name,
                email=data.email,
                course_id=data.course_id,
                institute=data.institute,
                role=role,
                status=AccountStatusEnum.PENDING,
                course_full_name=getattr(data, "course_full_name", None),
                course_key=getattr(data, "course_key", None),
                groups=getattr(data, "groups", None),
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
