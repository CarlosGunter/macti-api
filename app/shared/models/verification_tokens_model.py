# Módulo VerificationToken - Persistencia de Tokens de Seguridad
#
# Este modelo gestiona la creación y el estado de los tokens UUID enviados por
# correo electrónico. Actúa como el puente de seguridad entre la aprobación
# administrativa de una cuenta y el aprovisionamiento final en Keycloak y Moodle.

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.shared.models.auth_model import Auth


class VerificationToken(Base):
    """
    Representa un token de un solo uso para la validación de cuentas.

    Relaciones:
        - Pertenece a un registro de 'Auth' mediante auth_id.
    """

    __tablename__ = "MCT_verification_tokens"

    # Identificador único del token en base de datos
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Vinculación con la cuenta de usuario
    auth_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_auth.id", ondelete="CASCADE"), nullable=False
    )

    # El token UUID único que se envía en el enlace de correo
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # Trazabilidad temporal para auditoría y expiración
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Estado del token (False: Disponible, True: Utilizado)
    is_used: Mapped[bool] = mapped_column(Integer, default=0)

    # Relación bidireccional con el modelo de autenticación
    auth: Mapped["Auth"] = relationship("Auth", back_populates="verification_tokens")

    def __repr__(self):
        """Representación legible para logs de depuración."""
        return f"<VerificationToken(token='{self.token}', expires_at='{self.expires_at}', is_used={self.is_used})>"
