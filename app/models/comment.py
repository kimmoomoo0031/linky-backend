from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, ForeignKey, Index,
    String, DateTime, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.core.mixins import SoftDeleteMixin

if False:  # TYPE_CHECKING
    from app.models.post import Post
    from app.models.user import User


class Comment(SoftDeleteMixin, Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    parent_comment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("comments.id")
    )
    author_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )
    guest_actor_id: Mapped[str | None] = mapped_column(String(64))
    guest_nickname: Mapped[str | None] = mapped_column(String(12))
    guest_password_hash: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    post: Mapped[Post] = relationship(back_populates="comments")
    author: Mapped[User | None] = relationship()
    parent: Mapped[Comment | None] = relationship(
        back_populates="replies", remote_side="Comment.id"
    )
    replies: Mapped[list[Comment]] = relationship(back_populates="parent")

    __table_args__ = (
        CheckConstraint(
            "(author_id IS NOT NULL AND guest_actor_id IS NULL) "
            "OR (author_id IS NULL AND guest_actor_id IS NOT NULL)",
            name="chk_comment_author",
        ),
        Index("idx_comment_post", "post_id", "created_at"),
        Index(
            "idx_comment_parent", "parent_comment_id",
            postgresql_where="parent_comment_id IS NOT NULL",
        ),
    )

    @validates("content")
    def validate_content(self, _key: str, content: str) -> str:
        if len(content) < 1 or len(content) > 200:
            raise ValueError("コメントは1〜200文字")
        return content

    def is_owned_by(self, user_id: int) -> bool:
        return self.author_id is not None and self.author_id == user_id

    def is_guest_comment(self) -> bool:
        return self.author_id is None and self.guest_actor_id is not None
