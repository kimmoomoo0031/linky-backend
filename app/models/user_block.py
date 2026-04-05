from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, ForeignKey, Index,
    String, DateTime, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if False:  # TYPE_CHECKING
    from app.models.user import User


class UserBlock(Base):
    __tablename__ = "user_blocks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    blocker_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    blocked_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )
    blocked_guest_id: Mapped[str | None] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    blocker: Mapped[User] = relationship(
        back_populates="blocks_given", foreign_keys=[blocker_id]
    )
    blocked_user: Mapped[User | None] = relationship(foreign_keys=[blocked_user_id])

    __table_args__ = (
        CheckConstraint(
            "blocker_id IS DISTINCT FROM blocked_user_id",
            name="chk_no_self_block",
        ),
        CheckConstraint(
            "(blocked_user_id IS NOT NULL AND blocked_guest_id IS NULL) "
            "OR (blocked_user_id IS NULL AND blocked_guest_id IS NOT NULL)",
            name="chk_target_one_only",
        ),
        Index(
            "uniq_active_block_user", "blocker_id", "blocked_user_id",
            unique=True,
            postgresql_where="active = true AND blocked_user_id IS NOT NULL",
        ),
        Index(
            "uniq_active_block_guest", "blocker_id", "blocked_guest_id",
            unique=True,
            postgresql_where="active = true AND blocked_guest_id IS NOT NULL",
        ),
        Index("idx_user_blocks_list", "blocker_id", "active"),
    )

    def deactivate(self) -> None:
        self.active = False

    def reactivate(self) -> None:
        self.active = True
