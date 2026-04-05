from datetime import datetime

from sqlalchemy import BigInteger, Index, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GuestActor(Base):
    __tablename__ = "guest_actors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    guest_actor_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_guest_actor_ttl", "last_accessed_at"),
    )

    def touch(self) -> None:
        self.last_accessed_at = func.now()
