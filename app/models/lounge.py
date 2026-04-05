from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if False:  # TYPE_CHECKING
    from app.models.user import User
    from app.models.lounge_view import LoungeView
    from app.models.post import Post


class Lounge(Base):
    __tablename__ = "lounges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(12), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    creator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    creator: Mapped[User] = relationship(back_populates="created_lounges")
    lounge_views: Mapped[list[LoungeView]] = relationship(back_populates="lounge")
    posts: Mapped[list[Post]] = relationship(back_populates="lounge")

    __table_args__ = (
        Index("idx_lounge_name_lower", func.lower("name"), unique=True),
        Index("idx_lounge_creator", "creator_id"),
    )

    @validates("name")
    def validate_name(self, _key: str, name: str) -> str:
        if len(name) < 2 or len(name) > 12:
            raise ValueError("ラウンジ名は2〜12文字")
        return name

    @validates("description")
    def validate_description(self, _key: str, description: str) -> str:
        if len(description) < 5 or len(description) > 200:
            raise ValueError("紹介文は5〜200文字")
        return description
