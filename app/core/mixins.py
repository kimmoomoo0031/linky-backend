from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    deleted_by: Mapped[str | None] = mapped_column(String(20))

    def soft_delete(self, deleted_by: str) -> None:
        self.is_deleted = True
        self.deleted_by = deleted_by
