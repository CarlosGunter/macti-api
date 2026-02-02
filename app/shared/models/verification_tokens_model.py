from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models.users_model import UserAccounts


class VerificationToken(Base):
    __tablename__ = "MCT_verification_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("MCT_user_accounts.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_used: Mapped[int] = mapped_column(Integer, default=0)

    # Relaciones
    account: Mapped["UserAccounts"] = relationship(
        "UserAccounts", back_populates="verification_tokens"
    )

    def __repr__(self):
        return f"<VerificationToken(token='{self.token}', is_used={self.is_used})>"
