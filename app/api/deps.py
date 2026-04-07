from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme)) -> str:
    if not credentials:
        raise UnauthorizedError("COMMON_UNAUTHORIZED", "認証が必要です。")
    return credentials.credentials


def get_current_user(
    token: str = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> User:
    """保護API用: 有効な会員ユーザーを返す。"""
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "トークンが無効です。")

    role = payload.get("role")
    sub = payload.get("sub")
    if not sub or not role:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "トークンが無効です。")

    if role == "guest":
        # 会員専用の依存性のため、ゲストはアクセス不可。
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "トークンが無効です。")

    user = db.query(User).filter(User.id == int(sub), User.status == "ACTIVE").first()
    if not user:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "トークンが無効です。")

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """トークンが無ければNone、あれば検証後Userを返す。"""
    if not credentials:
        return None

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None

    role = payload.get("role")
    sub = payload.get("sub")
    if not sub or role != "user":
        return None

    return db.query(User).filter(User.id == int(sub), User.status == "ACTIVE").first()


class CurrentActor:
    """会員・ゲスト両方許可するAPIで使用する認証結果。"""

    def __init__(self, role: str, sub: str, user: User | None = None) -> None:
        self.role = role
        self.sub = sub
        self.user = user

    @property
    def is_guest(self) -> bool:
        return self.role == "guest"

    @property
    def actor_id(self) -> str:
        return self.sub


def get_current_actor(
    token: str = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> CurrentActor:
    """会員・ゲスト両方許可する保護API用。"""
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "トークンが無効です。")

    role = payload.get("role")
    sub = payload.get("sub")
    if not sub or not role:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "トークンが無効です。")

    if role == "guest":
        return CurrentActor(role="guest", sub=sub)

    user = db.query(User).filter(User.id == int(sub), User.status == "ACTIVE").first()
    if not user:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "トークンが無効です。")

    return CurrentActor(role="user", sub=sub, user=user)
