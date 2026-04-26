# Módulo JIDs - Identificadores de Integración Externa
#
# Este modelo centraliza los identificadores únicos del usuario en los
# sistemas externos: Keycloak (IAM), Moodle (LMS) y Jupyter Hub.
# Mantiene una relación 1:1 con la tabla de autenticación.

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.shared.models.auth_model import Auth


class JIDs(Base):
    """
    Representación en base de datos de los identificadores externos de un usuario.

    Esta tabla mantiene una relación 1:1 con MCT_auth, almacenando los IDs
    que el usuario posee en plataformas externas integradas con MACTI.

    Tabla: MCT_jids (según imagen aprobada por el PM)

    Relaciones:
        - Pertenece a un Auth mediante auth_id (relación 1:1 única)
    """

    __tablename__ = "MCT_jids"

    # ========== IDENTIFICACIÓN PRIMARIA ==========
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ========== RELACIÓN CON AUTENTICACIÓN ==========
    # Vinculación 1:1 con la cuenta de autenticación
    auth_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("MCT_auth.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # ========== IDENTIFICADORES DE INTEGRACIÓN EXTERNA ==========
    # kc_id: UUID de Keycloak (identidad centralizada IAM)
    kc_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    # moodle_id: ID numérico del usuario en Moodle (LMS)
    moodle_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # jupyter_id: ID del usuario en Jupyter Hub (entorno de ejecución)
    jupyter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ========== RELACIÓN INVERSA ==========
    # Relación 1:1 con Auth (un usuario tiene un solo registro de JIDs)
    auth: Mapped["Auth"] = relationship("Auth", back_populates="jids")

    def __repr__(self):
        """Representación legible para depuración y logs."""
        return f"<JIDs(auth_id={self.auth_id}, kc_id={self.kc_id}, moodle_id={self.moodle_id}, jupyter_id={self.jupyter_id})>"
