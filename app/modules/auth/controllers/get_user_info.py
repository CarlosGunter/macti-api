from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth.models import AccountRequest, MCTValidacion


class GetUserInfoController:
    @staticmethod
    def get_user_info(token: str, db: Session):
        try:
            validation = (
                db.query(MCTValidacion).filter(MCTValidacion.token == token).first()
            )

            if not validation:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "TOKEN_INVALIDO",
                        "message": "Token inválido",
                    },
                )

            fecha_expiracion = validation.fecha_expiracion
            if fecha_expiracion and datetime.now() > fecha_expiracion:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error_code": "TOKEN_EXPIRADO",
                        "message": "El token ha expirado",
                    },
                )

            account_request = (
                db.query(AccountRequest)
                .filter(AccountRequest.id == validation.account_id)
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
