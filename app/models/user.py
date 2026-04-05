from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Index, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if False:  # TYPE_CHECKING
    from app.models.local_credential import LocalCredential
    from app.models.auth_identity import AuthIdentity
    from app.models.refresh_token import RefreshToken
    from app.models.notification_setting import NotificationSetting
    from app.models.notification import Notification
    from app.models.lounge import Lounge
    from app.models.lounge_view import LoungeView
    from app.models.post import Post
    from app.models.user_block import UserBlock


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

    local_credential: Mapped[LocalCredential | None] = relationship(
        back_populates="user", uselist=False
    )
    auth_identities: Mapped[list[AuthIdentity]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user")
    notification_setting: Mapped[NotificationSetting | None] = relationship(
        back_populates="user", uselist=False
    )
    notifications: Mapped[list[Notification]] = relationship(back_populates="user")
    created_lounges: Mapped[list[Lounge]] = relationship(back_populates="creator")
    lounge_views: Mapped[list[LoungeView]] = relationship(back_populates="user")
    posts: Mapped[list[Post]] = relationship(back_populates="author")
    blocks_given: Mapped[list[UserBlock]] = relationship(
        back_populates="blocker", foreign_keys="UserBlock.blocker_id"
    )

    __table_args__ = (
        Index("idx_users_status", "status"),
    )

    @validates("nickname")
    def validate_nickname(self, _key: str, nickname: str | None) -> str | None:
        if nickname is not None and (len(nickname) < 2 or len(nickname) > 12):
            raise ValueError("ニックネームは2〜12文字")
        return nickname

    def withdraw(self, reason: str, reason_text: str | None = None) -> None:
        self.status = "WITHDRAWN"
        self.withdrawn_at = func.now()
        self.withdraw_reason = reason
        self.withdraw_reason_text = reason_text
        self.nickname = None

    def is_active(self) -> bool:
        return self.status == "ACTIVE"
