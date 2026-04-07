import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ── bcrypt (パスワード) ──

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT (Access Token) ──

def create_access_token(
    sub: str | int,
    role: str,
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(sub),
        "role": role,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iss": "linky-api",
        "aud": "linky-mobile",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """トークンをデコードしpayloadを返す。失敗時はJWTErrorをraiseする。"""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        audience="linky-mobile",
        issuer="linky-api",
    )


# ── HMAC-SHA256 (Refresh Token) ──

def generate_refresh_token_raw() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw: str) -> str:
    return hmac.HMAC(
        settings.REFRESH_TOKEN_SECRET.encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_refresh_token(raw: str, token_hash: str) -> bool:
    candidate = hash_refresh_token(raw)
    return hmac.compare_digest(candidate, token_hash)
