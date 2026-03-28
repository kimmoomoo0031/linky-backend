from datetime import datetime

from sqlalchemy import BigInteger, Index, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_norm: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    nickname: Mapped[str | None] = mapped_column(String(12), unique=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False, server_default="user")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="local")
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdraw_reason: Mapped[str | None] = mapped_column(String(30))
    withdraw_reason_text: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_users_status", "status"),
    )
