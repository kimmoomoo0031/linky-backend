import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token_raw,
    hash_refresh_token,
    verify_refresh_token,
)
from app.models.guest_actor import GuestActor
from app.models.refresh_token import RefreshToken
from app.models.email_verification_session import EmailVerificationSession
from app.schemas.auth import TokenData

VERIFICATION_CODE_LENGTH = 4
VERIFICATION_TTL_SECONDS = 180
VERIFICATION_MAX_ATTEMPTS = 5
VERIFICATION_MAX_RESENDS = 5
VERIFICATION_LOCK_SECONDS = 600
VERIFICATION_COOLDOWN_SECONDS = 60


# ── Refresh Token ──

def issue_tokens(db: Session, user_id: int, role: str = "user") -> tuple[str, str]:
    """Access Token + Refresh Token を発行し、DB に保存する。raw refresh token を返す。"""
    access = create_access_token(sub=user_id, role=role)
    raw_refresh = generate_refresh_token_raw()
    token_hash = hash_refresh_token(raw_refresh)

    now = datetime.now(timezone.utc)
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        revoked=False,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    db.flush()

    _enforce_max_tokens(db, user_id)

    return access, raw_refresh


def _enforce_max_tokens(db: Session, user_id: int) -> None:
    """ユーザーあたりの有効トークンを最大件数に制限する（古い順に revoke）。"""
    active = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .order_by(RefreshToken.created_at.desc())
        .all()
    )
    if len(active) > settings.REFRESH_TOKEN_MAX_PER_USER:
        for old in active[settings.REFRESH_TOKEN_MAX_PER_USER:]:
            old.revoke()


def build_token_data(access: str, raw_refresh: str | None = None) -> TokenData:
    return TokenData(
        access_token=access,
        refresh_token=raw_refresh,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def verify_and_rotate_refresh(db: Session, raw_token: str) -> tuple[RefreshToken, str, str] | None:
    """Refresh Token を検証し、回転（旧 revoke + 新発行）する。成功時 (old_rt, new_access, new_raw_refresh)。"""
    candidate_hash = hash_refresh_token(raw_token)
    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == candidate_hash, RefreshToken.revoked.is_(False))
        .first()
    )
    if not rt:
        return None
    if rt.is_expired(datetime.now(timezone.utc)):
        rt.revoke()
        return None

    rt.revoke()

    new_access, new_raw = issue_tokens(db, rt.user_id)
    return rt, new_access, new_raw


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    candidate_hash = hash_refresh_token(raw_token)
    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == candidate_hash, RefreshToken.revoked.is_(False))
        .first()
    )
    if not rt:
        return False
    rt.revoke()
    return True


# ── Guest ──

def get_or_create_guest(db: Session, guest_actor_id: str | None) -> GuestActor:
    if guest_actor_id:
        existing = db.query(GuestActor).filter(GuestActor.guest_actor_id == guest_actor_id).first()
        if existing:
            existing.touch()
            return existing

    new_id = secrets.token_urlsafe(32)
    guest = GuestActor(guest_actor_id=new_id)
    db.add(guest)
    db.flush()
    return guest


def create_guest_access_token(guest_actor_id: str) -> str:
    return create_access_token(sub=guest_actor_id, role="guest")


# ── Email Verification Session ──

def _generate_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(VERIFICATION_CODE_LENGTH))


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def create_verification_session(db: Session, email: str) -> tuple[EmailVerificationSession, str]:
    """既存セッションを無効化し、新規セッションを作成する。(session, plain_code) を返す。"""
    db.query(EmailVerificationSession).filter(
        EmailVerificationSession.email == email.strip().lower(),
        EmailVerificationSession.verified.is_(False),
    ).delete()

    code = _generate_code()
    now = datetime.now(timezone.utc)
    session = EmailVerificationSession(
        email=email.strip().lower(),
        code_hash=_hash_code(code),
        attempt_count=0,
        resend_count=0,
        last_sent_at=now,
        expires_at=now + timedelta(seconds=VERIFICATION_TTL_SECONDS),
        verified=False,
    )
    db.add(session)
    db.flush()
    return session, code


def get_active_session(db: Session, email: str) -> EmailVerificationSession | None:
    return (
        db.query(EmailVerificationSession)
        .filter(
            EmailVerificationSession.email == email.strip().lower(),
            EmailVerificationSession.verified.is_(False),
        )
        .order_by(EmailVerificationSession.created_at.desc())
        .first()
    )


def resend_verification_code(db: Session, session: EmailVerificationSession) -> tuple[str, int]:
    """コードを再発行する。(plain_code, resend_remaining) を返す。"""
    code = _generate_code()
    now = datetime.now(timezone.utc)
    session.renew_code(_hash_code(code), now, VERIFICATION_TTL_SECONDS)
    session.increment_resend()
    remaining = VERIFICATION_MAX_RESENDS - session.resend_count
    return code, remaining


def verify_code(db: Session, session: EmailVerificationSession, code: str) -> bool:
    """コードを検証する。成功時 True, 失敗時 False。attempt_count を加算する。"""
    session.increment_attempt()
    if session.attempt_count >= VERIFICATION_MAX_ATTEMPTS:
        session.lock(datetime.now(timezone.utc), VERIFICATION_LOCK_SECONDS)

    if _hash_code(code) == session.code_hash:
        session.mark_verified()
        return True
    return False


def create_reset_token(db: Session, session: EmailVerificationSession) -> str:
    """パスワードリセット用の reset_token を生成し、ハッシュを保存する。raw token を返す。"""
    raw = secrets.token_urlsafe(32)
    session.set_reset_token(hashlib.sha256(raw.encode()).hexdigest())
    return raw


def verify_reset_token(db: Session, raw_token: str) -> EmailVerificationSession | None:
    """reset_token を検証し、対応する verified セッションを返す。"""
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return (
        db.query(EmailVerificationSession)
        .filter(
            EmailVerificationSession.reset_token_hash == token_hash,
            EmailVerificationSession.verified.is_(True),
        )
        .first()
    )
