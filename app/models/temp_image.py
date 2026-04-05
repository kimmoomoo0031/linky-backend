from datetime import datetime

from sqlalchemy import BigInteger, Index, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TempImage(Base):
    __tablename__ = "temp_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    temp_image_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    uploader_id: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    temp_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_temp_image_uploader", "uploader_id", "created_at"),
        Index("idx_temp_image_cleanup", "expires_at"),
    )

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now
