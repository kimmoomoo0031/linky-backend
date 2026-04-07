from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TempImageResponseData(BaseModel):
    temp_image_id: str
    temp_url: str
    expires_at: datetime
