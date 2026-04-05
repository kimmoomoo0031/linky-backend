from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, ForeignKey, Index,
    Integer, String, Text, DateTime, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if False:  # TYPE_CHECKING
    from app.models.lounge import Lounge
    from app.models.user import User
    from app.models.best_post import BestPost
    from app.models.post_reaction import PostReaction
    from app.models.post_image import PostImage
    from app.models.comment import Comment


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lounge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lounges.id"), nullable=False
    )
    author_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )
    guest_actor_id: Mapped[str | None] = mapped_column(String(64))
    guest_nickname: Mapped[str | None] = mapped_column(String(12))
    guest_password_hash: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    content_plain: Mapped[str] = mapped_column(Text, nullable=False)
    has_image: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    dislike_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    lounge: Mapped[Lounge] = relationship(back_populates="posts")
    author: Mapped[User | None] = relationship(back_populates="posts")
    best_post: Mapped[BestPost | None] = relationship(
        back_populates="post", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )
    reactions: Mapped[list[PostReaction]] = relationship(
        back_populates="post", cascade="all, delete-orphan", passive_deletes=True
    )
    images: Mapped[list[PostImage]] = relationship(
        back_populates="post", cascade="all, delete-orphan", passive_deletes=True
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="post", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(
            "(author_id IS NOT NULL AND guest_actor_id IS NULL) "
            "OR (author_id IS NULL AND guest_actor_id IS NOT NULL)",
            name="chk_post_author",
        ),
        Index("idx_post_lounge_created", "lounge_id", "created_at"),
        Index("idx_post_author", "author_id", postgresql_where="author_id IS NOT NULL"),
    )

    @validates("title")
    def validate_title(self, _key: str, title: str) -> str:
        if len(title) < 1 or len(title) > 50:
            raise ValueError("タイトルは1〜50文字")
        return title

    def is_owned_by(self, user_id: int) -> bool:
        return self.author_id is not None and self.author_id == user_id

    def is_guest_post(self) -> bool:
        return self.author_id is None and self.guest_actor_id is not None

    def increment_view(self) -> None:
        self.view_count += 1

    def increment_comment_count(self) -> None:
        self.comment_count += 1

    def decrement_comment_count(self) -> None:
        if self.comment_count > 0:
            self.comment_count -= 1
