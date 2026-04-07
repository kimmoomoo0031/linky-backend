from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, field_validator


# ── Request ──

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 64:
            raise ValueError("パスワードは8〜64文字で入力してください。")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("パスワードには英字を含めてください。")
        if not re.search(r"[0-9]", v):
            raise ValueError("パスワードには数字を含めてください。")
        if not re.fullmatch(r"[A-Za-z0-9!@]+", v):
            raise ValueError("パスワードに使用できない文字が含まれています。")
        return v

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 12:
            raise ValueError("ニックネームは2〜12文字で入力してください。")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GuestLoginRequest(BaseModel):
    guest_actor_id: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordForgotRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    reset_token: str
    new_password: str
    new_password_confirm: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 64:
            raise ValueError("パスワードは8〜64文字で入力してください。")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("パスワードには英字を含めてください。")
        if not re.search(r"[0-9]", v):
            raise ValueError("パスワードには数字を含めてください。")
        if not re.fullmatch(r"[A-Za-z0-9!@]+", v):
            raise ValueError("パスワードに使用できない文字が含まれています。")
        return v


class VerifyEmailSendRequest(BaseModel):
    email: EmailStr


class VerifyEmailResendRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


# ── Response (data 部分) ──

class TokenData(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_in: int


class UserData(BaseModel):
    id: int
    email: str
    nickname: str | None
    role: str


class LoginResponseData(BaseModel):
    tokens: TokenData
    user: UserData


class GuestLoginResponseData(BaseModel):
    tokens: TokenData
    guest_actor_id: str


class LogoutResponseData(BaseModel):
    logged_out: bool = True


class RefreshResponseData(BaseModel):
    tokens: TokenData


class PasswordForgotResponseData(BaseModel):
    accepted: bool = True


class PasswordResetResponseData(BaseModel):
    password_reset: bool = True


class VerifyEmailSendResponseData(BaseModel):
    expires_in: int


class VerifyEmailResendResponseData(BaseModel):
    expires_in: int
    resend_remaining: int


class VerifyEmailResponseData(BaseModel):
    verified: bool = True
    reset_token: str | None = None
