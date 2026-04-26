# Módulo UserProfiles - Información de Perfil de Usuario
#
# Este modelo almacena la información detallada del perfil del usuario,
# manteniendo una relación 1:1 con la tabla de autenticación.

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.enums.status_enum import AccountStatusEnum

if TYPE_CHECKING:
    from app.shared.models.users_model import Auth


class UserProfile(Base):
    """
    Representación en base de datos del perfil detallado de un usuario.

    Esta tabla mantiene una relación 1:1 con MCT_auth, almacenando información
    personal que complementa la cuenta de autenticación.

    Relaciones:
        - Pertenece a un Auth mediante auth_id (relación 1:1 única)
    """

    __tablename__ = "MCT_user_profiles"

    # Identificador único del perfil
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Vinculación con la cuenta de autenticación (única por usuario)
    auth_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("MCT_auth.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Información personal del usuario
    name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    institute: Mapped[InstitutesEnum] = mapped_column(
        Enum(InstitutesEnum, name="institutes_enum"), nullable=False
    )

    # ========== ESTADO DE LA CUENTA ==========
    # PENDING -> APPROVED -> CREATED / REJECTED
    status: Mapped[AccountStatusEnum] = mapped_column(
        Enum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.PENDING,
        nullable=False,
    )

    # Auditoría
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relación inversa hacia el modelo de autenticación
    auth: Mapped["Auth"] = relationship("Auth", back_populates="profile")

    def __repr__(self):
        """Retorna una representación legible del objeto de perfil."""
        return f"<UserProfile(name='{self.name} {self.last_name}', institute='{self.institute.value}')>"
