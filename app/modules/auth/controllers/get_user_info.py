# Módulo GetUserInfoController - Recuperación de Contexto de Validación
# Este controlador resuelve la identidad de un usuario a partir de un token.
# Permite que el front-end recupere datos de forma segura durante el onboarding.

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.shared.models.users_model import UserAccounts
from app.shared.models.verification_tokens_model import VerificationToken


class GetUserInfoController:
    """
    Controlador encargado de validar tokens de verificación y retornar
    la información del usuario asociado.
    """

    @staticmethod
    def get_user_info(token: str, db: Session):
        """
        Recupera los datos básicos del usuario mediante un token.

        Flujo de validación:
        1. Busca el token en la tabla VerificationToken.
        2. Verifica la expiración.
        3. Localiza la cuenta de usuario vinculada.
        """
        try:
            # 1. Búsqueda del token en la base de datos
            validation = (
                db.query(VerificationToken)
                .filter(VerificationToken.token == token)
                .first()
            )

            # Error si el token no existe en el sistema
            if not validation:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "TOKEN_INVALIDO",
                        "message": "El token proporcionado no existe o es incorrecto",
                    },
                )

            # 2. Validación de vigencia (Expiración)
            expires_at = validation.expires_at
            if expires_at and datetime.now() > expires_at:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error_code": "TOKEN_EXPIRADO",
                        "message": "El token ha expirado. Por favor, solicite una nueva aprobación.",
                    },
                )

            # 3. Recuperación de la información del usuario
            account_request = (
                db.query(UserAccounts)
                .filter(UserAccounts.id == validation.account_id)
                .first()
            )

            # Error de integridad: Token existe pero el usuario no
            if not account_request:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": "NO_ENCONTRADO",
                        "message": "No se encontró un usuario vinculado a este token",
                    },
                )

            # Retorno de datos para el Front-end:
            # Permite pre-llenar los campos de registro en la interfaz de usuario.
            return {
                "id": account_request.id,
                "email": account_request.email,
                "name": account_request.name,
                "last_name": account_request.last_name,
                "institute": account_request.institute,
            }

        except HTTPException as httpe:
            # Propagación de excepciones controladas para la API
            raise httpe

        except Exception as e:
            # Manejo de errores a nivel de infraestructura o base de datos
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "DB_ERROR",
                    "message": f"Error inesperado al consultar la base de datos: {e}",
                },
            ) from e
