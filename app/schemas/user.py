from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, field_validator


# ── Response ──

class ProfileResponseData(BaseModel):
    id: int
    email: str
    nickname: str | None
    role: str
    auth_provider: str


class UpdateProfileResponseData(BaseModel):
    updated: bool = True


class WithdrawResponseData(BaseModel):
    withdrawn: bool = True


# ── Request ──

WITHDRAW_REASONS = Literal[
    "not_useful",
    "found_alternative",
    "too_many_notifications",
    "privacy_concern",
    "rarely_use",
    "other",
]


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    current_password: str | None = None
    new_password: str | None = None
    new_password_confirm: str | None = None

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str | None) -> str | None:
        if v is not None and (len(v) < 2 or len(v) > 12):
            raise ValueError("ニックネームは2〜12文字で入力してください。")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) < 8 or len(v) > 64:
            raise ValueError("パスワードは8〜64文字で入力してください。")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("パスワードには英字を含めてください。")
        if not re.search(r"[0-9]", v):
            raise ValueError("パスワードには数字を含めてください。")
        if not re.fullmatch(r"[A-Za-z0-9!@]+", v):
            raise ValueError("パスワードに使用できない文字が含まれています。")
        return v


class WithdrawRequest(BaseModel):
    current_password: str | None = None
    reason: WITHDRAW_REASONS
    reason_text: str | None = None

    @field_validator("reason_text")
    @classmethod
    def validate_reason_text(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 500:
            raise ValueError("自由入力テキストは最大500文字です。")
        return v
