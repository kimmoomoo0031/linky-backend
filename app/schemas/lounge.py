from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, field_validator


# ── Request ──

class CreateLoungeRequest(BaseModel):
    name: str
    description: str
    cover_image_id: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 12:
            raise ValueError("ラウンジ名は2〜12文字で入力してください。")
        if not re.fullmatch(r"[A-Za-zぁ-んァ-ヶ\u4E00-\u9FFFー\-]+", v):
            raise ValueError("ラウンジ名は英語・日本語・ハイフンのみ使用できます。")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if len(v) < 5 or len(v) > 200:
            raise ValueError("紹介文は5〜200文字で入力してください。")
        return v


# ── Response ──

class CreateLoungeResponseData(BaseModel):
    id: int
    name: str
    created_at: datetime


class LoungeCardResponseData(BaseModel):
    id: int
    name: str
    thumbnail_url: str | None
    total_post_count: int


class LoungeListResponseData(BaseModel):
    lounges: list[LoungeCardResponseData]


class LoungeDetailResponseData(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    total_post_count: int
    cover_image_url: str | None


class PostListItemResponseData(BaseModel):
    id: int
    title: str
    created_at: datetime
    nickname: str
    view_count: int
    like_count: int
    comment_count: int
    has_image: bool
    is_guest: bool
    is_best: bool


class PostListResponseData(BaseModel):
    posts: list[PostListItemResponseData]
    cursor: str | None
    has_next: bool


class PostSearchResponseData(BaseModel):
    posts: list[PostListItemResponseData]
    total_count: int
    cursor: str | None
    has_next: bool
