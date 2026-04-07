from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.auth_identity import AuthIdentity
from app.models.local_credential import LocalCredential
from app.models.notification_setting import NotificationSetting
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.core.security import hash_password


def get_by_email_norm(db: Session, email: str) -> User | None:
    norm = email.strip().lower()
    return db.query(User).filter(User.email_norm == norm).first()


def get_by_nickname(db: Session, nickname: str) -> User | None:
    return db.query(User).filter(User.nickname == nickname).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_local_user(
    db: Session,
    *,
    email: str,
    password: str,
    nickname: str,
) -> User:
    """ローカル会員登録。User + LocalCredential + NotificationSetting を同一トランザクションで作成する。"""
    user = User(
        email=email,
        email_norm=email.strip().lower(),
        nickname=nickname,
        role="user",
        status="ACTIVE",
        auth_provider="local",
    )
    db.add(user)
    db.flush()

    credential = LocalCredential(
        user_id=user.id,
        password_hash=hash_password(password),
    )
    db.add(credential)

    setting = NotificationSetting(
        user_id=user.id,
        comment_notification_enabled=True,
        reply_notification_enabled=True,
        best_post_notification_enabled=True,
    )
    db.add(setting)

    return user


def update_password(db: Session, user: User, new_password: str) -> None:
    cred = db.query(LocalCredential).filter(LocalCredential.user_id == user.id).first()
    if cred:
        cred.password_hash = hash_password(new_password)
        cred.updated_at = func.now()


def update_nickname(db: Session, user: User, nickname: str) -> None:
    user.nickname = nickname


def withdraw_user(db: Session, user: User, reason: str, reason_text: str | None = None) -> None:
    """退会処理。User 状態変更 + auth_identities 無効化 + refresh_tokens 全 revoke。"""
    user.withdraw(reason, reason_text)

    db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).update({"active": False})

    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked.is_(False),
    ).update({"revoked": True})
