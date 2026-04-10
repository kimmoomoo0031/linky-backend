from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if False:  # TYPE_CHECKING
    from app.models.user import User
    from app.models.lounge import Lounge


class LoungeView(Base):
    __tablename__ = "lounge_views"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    lounge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lounges.id"), nullable=False
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="lounge_views")
    lounge: Mapped[Lounge] = relationship(back_populates="lounge_views")

    __table_args__ = (
        UniqueConstraint("user_id", "lounge_id", name="uniq_user_lounge"),
        Index("idx_lounge_views_recent", "user_id", "viewed_at"),
    )

    def update_viewed_at(self) -> None:
        self.viewed_at = func.now()
