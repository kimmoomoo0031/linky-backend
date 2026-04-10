from datetime import datetime, timedelta

from sqlalchemy import BigInteger, Boolean, Index, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmailVerificationSession(Base):
    __tablename__ = "email_verification_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    resend_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    reset_token_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_email_verify_email", "email", "verified"),
    )

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now

    def increment_attempt(self) -> None:
        self.attempt_count += 1

    def increment_resend(self) -> None:
        self.resend_count += 1

    def lock(self, now: datetime, lock_seconds: int) -> None:
        self.locked_until = now + timedelta(seconds=lock_seconds)

    def unlock(self) -> None:
        self.attempt_count = 0
        self.locked_until = None

    def mark_verified(self) -> None:
        self.verified = True

    def renew_code(self, new_code_hash: str, now: datetime, ttl_seconds: int) -> None:
        self.code_hash = new_code_hash
        self.last_sent_at = now
        self.expires_at = now + timedelta(seconds=ttl_seconds)

    def set_reset_token(self, token_hash: str) -> None:
        self.reset_token_hash = token_hash

    def invalidate_reset_token(self) -> None:
        self.reset_token_hash = None
