# Módulo VerificationToken - Persistencia de Tokens de Seguridad
#
# Este modelo gestiona la creación y el estado de los tokens UUID enviados por
# correo electrónico. Actúa como el puente de seguridad entre la aprobación
# administrativa de una cuenta y el aprovisionamiento final en Keycloak y Moodle.

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models.users_model import UserAccounts


class VerificationToken(Base):
    """
    Representa un token de un solo uso para la validación de cuentas.

    Relaciones:
        - Pertenece a un registro de 'UserAccounts' mediante account_id.
    """

    __tablename__ = "MCT_verification_tokens"

    # Identificador único del token en base de datos
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Vinculación con la solicitud de cuenta pendiente
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_user_accounts.id"), nullable=False
    )

    # El token UUID único que se envía en el enlace de correo
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # Trazabilidad temporal para auditoría y expiración
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Estado del token (0: Disponible, 1: Utilizado)
    is_used: Mapped[int] = mapped_column(Integer, default=0)

    # Relación bidireccional con el modelo de cuentas de usuario
    account: Mapped["UserAccounts"] = relationship(
        "UserAccounts", back_populates="verification_tokens"
    )

    def __repr__(self):
        """Representación legible para logs de depuración."""
        return f"<VerificationToken(token='{self.token}', is_used={self.is_used})>"
