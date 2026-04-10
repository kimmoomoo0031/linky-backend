import tempfile

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_actor, CurrentActor
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.crud import crud_upload
from app.db.session import get_db
from app.schemas.common import SuccessResponse
from app.schemas.upload import TempImageResponseData

router = APIRouter()


@router.post("/images/temp", status_code=201)
async def upload_temp_image(
    file: UploadFile = File(...),
    actor: CurrentActor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    if file.content_type not in crud_upload.ALLOWED_MIME_TYPES:
        raise BadRequestError(
            "UPLOAD_UNSUPPORTED_FORMAT",
            "対応していない画像形式です。JPEG / PNG / WebP / GIF のみ使用できます。",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
        size = 0
        while chunk := await file.read(8192):
            size += len(chunk)
            if size > settings.UPLOAD_MAX_FILE_SIZE:
                raise BadRequestError(
                    "UPLOAD_FILE_TOO_LARGE",
                    "ファイルサイズが上限（10MB）を超えています。",
                )
            tmp.write(chunk)
        tmp_path = tmp.name

    record = crud_upload.save_temp_image(
        db,
        uploader_id=actor.actor_id,
        tmp_path=tmp_path,
        file_size=size,
        mime_type=file.content_type,
    )

    return SuccessResponse(
        data=TempImageResponseData(
            temp_image_id=record.temp_image_id,
            temp_url=record.temp_url,
            expires_at=record.expires_at,
        )
    )
