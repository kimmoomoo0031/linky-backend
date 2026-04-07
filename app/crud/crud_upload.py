import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage import storage
from app.models.temp_image import TempImage


ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


def save_temp_image(
    db: Session,
    *,
    uploader_id: str,
    tmp_path: str,
    file_size: int,
    mime_type: str,
) -> TempImage:
    """temp 画像を保存し、DB レコードを作成する。20 枚上限を超えた場合は最古を自動削除。"""
    _enforce_max_temp(db, uploader_id)

    image_id = uuid.uuid4().hex
    ext = MIME_TO_EXT[mime_type]
    dest_key = f"temp/{uploader_id}/{image_id}.{ext}"

    url = storage.save(tmp_path, dest_key)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.UPLOAD_TEMP_EXPIRE_HOURS)

    record = TempImage(
        temp_image_id=image_id,
        uploader_id=uploader_id,
        file_path=dest_key,
        temp_url=url,
        file_size=file_size,
        mime_type=mime_type,
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()
    return record


def _enforce_max_temp(db: Session, uploader_id: str) -> None:
    """20 枚上限を超えた場合、最も古い temp を削除する。"""
    count = (
        db.query(func.count(TempImage.id))
        .filter(TempImage.uploader_id == uploader_id)
        .scalar()
        or 0
    )
    if count < settings.UPLOAD_TEMP_MAX_PER_USER:
        return

    oldest = (
        db.query(TempImage)
        .filter(TempImage.uploader_id == uploader_id)
        .order_by(TempImage.created_at.asc())
        .first()
    )
    if oldest:
        storage.delete(oldest.file_path)
        db.delete(oldest)
        db.flush()


def get_by_temp_id(db: Session, temp_image_id: str) -> TempImage | None:
    return db.query(TempImage).filter(TempImage.temp_image_id == temp_image_id).first()


def get_by_uploader(db: Session, uploader_id: str) -> list[TempImage]:
    return (
        db.query(TempImage)
        .filter(TempImage.uploader_id == uploader_id)
        .order_by(TempImage.created_at.desc())
        .all()
    )


def delete_temp(db: Session, record: TempImage) -> None:
    storage.delete(record.file_path)
    db.delete(record)
