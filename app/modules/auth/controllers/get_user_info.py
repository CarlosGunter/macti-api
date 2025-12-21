from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.shared.models.users_model import UserAccounts
from app.shared.models.verification_tokens_model import VerificationToken


class GetUserInfoController:
    @staticmethod
    def get_user_info(token: str, db: Session):
        try:
            validation = (
                db.query(VerificationToken)
                .filter(VerificationToken.token == token)
                .first()
            )

            if not validation:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "TOKEN_INVALIDO",
                        "message": "Token inválido",
                    },
                )

            expires_at = validation.expires_at
            if expires_at and datetime.now() > expires_at:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error_code": "TOKEN_EXPIRADO",
                        "message": "El token ha expirado",
                    },
                )

            account_request = (
                db.query(UserAccounts)
                .filter(UserAccounts.id == validation.account_id)
                .first()
            )

            if not account_request:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "NO_ENCONTRADO",
                        "message": "No se encontró un usuario con este correo",
                    },
                )

            return {
                "id": account_request.id,
                "email": account_request.email,
                "name": account_request.name,
                "last_name": account_request.last_name,
                "institute": account_request.institute,
            }

        except HTTPException as httpe:
            raise httpe

        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "DB_ERROR",
                    "message": f"Error de base de datos: {e}",
                },
            ) from e
