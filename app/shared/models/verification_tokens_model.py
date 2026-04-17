# Módulo VerificationToken - Persistencia de Tokens de Seguridad
#
# Este modelo gestiona la creación y el estado de los tokens UUID enviados por
# correo electrónico.

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.shared.models.users_model import UserAccounts


class VerificationToken(Base):
    """
    Representa un token de un solo uso para la validación de cuentas.

    Relaciones:
        - Pertenece a un registro de 'UserAccounts' mediante auth_id.
    """

    __tablename__ = "MCT_verification_tokens"

    # Identificador único del token en base de datos
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Vinculación con la cuenta de usuario
    auth_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_auth.id"), nullable=False
    )

    # El token UUID único que se envía en el enlace de correo
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # Fecha de expiración del token
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relación bidireccional con el modelo de cuentas de usuario
    user: Mapped["UserAccounts"] = relationship(
        "UserAccounts", back_populates="verification_tokens"
    )

    def __repr__(self):
        """Representación legible para logs de depuración."""
        return (
            f"<VerificationToken(token='{self.token}', expires_at='{self.expires_at}')>"
        )
