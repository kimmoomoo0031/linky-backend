from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.email import send_verification_email
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    RateLimitError,
    UnauthorizedError,
)
from app.core.security import verify_password
from app.crud import crud_auth, crud_user
from app.db.session import get_db
from app.schemas.auth import (
    GuestLoginRequest,
    GuestLoginResponseData,
    LoginRequest,
    LoginResponseData,
    LogoutRequest,
    LogoutResponseData,
    PasswordForgotRequest,
    PasswordForgotResponseData,
    PasswordResetRequest,
    PasswordResetResponseData,
    RefreshRequest,
    RefreshResponseData,
    RegisterRequest,
    TokenData,
    UserData,
    VerifyEmailRequest,
    VerifyEmailResendRequest,
    VerifyEmailResendResponseData,
    VerifyEmailResponseData,
    VerifyEmailSendRequest,
    VerifyEmailSendResponseData,
)
from app.schemas.common import SuccessResponse

router = APIRouter()


# ── POST /auth/register ──

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if crud_user.get_by_email_norm(db, body.email):
        raise ConflictError("AUTH_EMAIL_DUPLICATED", "既に登録済みのメールアドレスです。")

    if crud_user.get_by_nickname(db, body.nickname):
        raise ConflictError("AUTH_NICKNAME_DUPLICATED", "既に使用されているニックネームです。")

    user = crud_user.create_local_user(
        db, email=body.email, password=body.password, nickname=body.nickname,
    )
    access, raw_refresh = crud_auth.issue_tokens(db, user.id)

    return SuccessResponse(
        data=LoginResponseData(
            tokens=crud_auth.build_token_data(access, raw_refresh),
            user=UserData(id=user.id, email=user.email, nickname=user.nickname, role=user.role),
        )
    )


# ── POST /auth/login ──

@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = crud_user.get_by_email_norm(db, body.email)
    if not user or not user.is_active():
        raise UnauthorizedError(
            "AUTH_INVALID_CREDENTIALS",
            "このアカウントではログインできません。別のログイン方法を試すか、パスワードを再設定してください。",
        )

    if user.auth_provider != "local" or not user.local_credential:
        raise UnauthorizedError(
            "AUTH_INVALID_CREDENTIALS",
            "このアカウントではログインできません。別のログイン方法を試すか、パスワードを再設定してください。",
        )

    if not verify_password(body.password, user.local_credential.password_hash):
        raise UnauthorizedError(
            "AUTH_INVALID_CREDENTIALS",
            "このアカウントではログインできません。別のログイン方法を試すか、パスワードを再設定してください。",
        )

    access, raw_refresh = crud_auth.issue_tokens(db, user.id)

    return SuccessResponse(
        data=LoginResponseData(
            tokens=crud_auth.build_token_data(access, raw_refresh),
            user=UserData(id=user.id, email=user.email, nickname=user.nickname, role=user.role),
        )
    )


# ── POST /auth/guest ──

@router.post("/guest")
def guest_login(body: GuestLoginRequest, db: Session = Depends(get_db)):
    guest = crud_auth.get_or_create_guest(db, body.guest_actor_id)
    access = crud_auth.create_guest_access_token(guest.guest_actor_id)

    return SuccessResponse(
        data=GuestLoginResponseData(
            tokens=TokenData(
                access_token=access,
                token_type="Bearer",
                expires_in=60 * 60,
            ),
            guest_actor_id=guest.guest_actor_id,
        )
    )


# ── POST /auth/logout ──

@router.post("/logout")
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    crud_auth.revoke_refresh_token(db, body.refresh_token)
    return SuccessResponse(data=LogoutResponseData())


# ── POST /auth/refresh ──

@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    result = crud_auth.verify_and_rotate_refresh(db, body.refresh_token)
    if not result:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "refresh_tokenは期限切れか無効です。")

    _old_rt, new_access, new_raw = result
    return SuccessResponse(
        data=RefreshResponseData(tokens=crud_auth.build_token_data(new_access, new_raw)),
    )


# ── POST /auth/password/forgot ──

@router.post("/password/forgot")
async def password_forgot(body: PasswordForgotRequest, db: Session = Depends(get_db)):
    user = crud_user.get_by_email_norm(db, body.email)
    if user and user.is_active() and user.auth_provider == "local":
        session, code = crud_auth.create_verification_session(db, body.email)
        await send_verification_email(body.email, code)

    return SuccessResponse(data=PasswordForgotResponseData())


# ── POST /auth/password/reset ──

@router.post("/password/reset")
def password_reset(body: PasswordResetRequest, db: Session = Depends(get_db)):
    if body.new_password != body.new_password_confirm:
        raise BadRequestError(
            "AUTH_INVALID_INPUT",
            "new_passwordが要件を満たしていないか、確認用パスワードと一致しません。",
            details=[{"field": "new_password_confirm", "message": "パスワードが一致しません。"}],
        )

    session = crud_auth.verify_reset_token(db, body.reset_token)
    if not session:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "reset_tokenは期限切れか無効です。")

    user = crud_user.get_by_email_norm(db, session.email)
    if not user:
        raise UnauthorizedError("AUTH_TOKEN_INVALID", "reset_tokenは期限切れか無効です。")

    crud_user.update_password(db, user, body.new_password)
    session.invalidate_reset_token()

    return SuccessResponse(data=PasswordResetResponseData())


# ── POST /auth/verify-email/send ──

@router.post("/verify-email/send")
async def verify_email_send(body: VerifyEmailSendRequest, db: Session = Depends(get_db)):
    session, code = crud_auth.create_verification_session(db, body.email)
    await send_verification_email(body.email, code)

    return SuccessResponse(
        data=VerifyEmailSendResponseData(expires_in=crud_auth.VERIFICATION_TTL_SECONDS),
    )


# ── POST /auth/verify-email/resend ──

@router.post("/verify-email/resend")
async def verify_email_resend(body: VerifyEmailResendRequest, db: Session = Depends(get_db)):
    session = crud_auth.get_active_session(db, body.email)
    if not session:
        raise BadRequestError("AUTH_INVALID_INPUT", "有効な認証セッションがありません。")

    now = datetime.now(timezone.utc)

    if session.last_sent_at and (now - session.last_sent_at).total_seconds() < crud_auth.VERIFICATION_COOLDOWN_SECONDS:
        raise RateLimitError(
            "AUTH_RATE_LIMITED",
            "再送信クールダウン中、またはリクエスト回数が上限を超えました。しばらくしてから再試行してください。",
        )

    if session.resend_count >= crud_auth.VERIFICATION_MAX_RESENDS:
        raise RateLimitError(
            "AUTH_RATE_LIMITED",
            "再送信クールダウン中、またはリクエスト回数が上限を超えました。しばらくしてから再試行してください。",
        )

    code, remaining = crud_auth.resend_verification_code(db, session)
    await send_verification_email(body.email, code)

    return SuccessResponse(
        data=VerifyEmailResendResponseData(
            expires_in=crud_auth.VERIFICATION_TTL_SECONDS,
            resend_remaining=remaining,
        ),
    )


# ── POST /auth/verify-email ──

@router.post("/verify-email")
def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    session = crud_auth.get_active_session(db, body.email)
    if not session:
        raise BadRequestError("AUTH_INVALID_INPUT", "認証コードが一致しないか、有効期限が切れています。")

    now = datetime.now(timezone.utc)

    if session.locked_until and now < session.locked_until:
        raise RateLimitError(
            "AUTH_RATE_LIMITED",
            "入力試行回数が上限を超えたか、再送信クールダウン中です。しばらくしてから再試行してください。",
        )
    elif session.locked_until and now >= session.locked_until:
        session.unlock()

    if session.is_expired(now):
        raise BadRequestError("AUTH_INVALID_INPUT", "認証コードが一致しないか、有効期限が切れています。")

    ok = crud_auth.verify_code(db, session, body.code)
    if not ok:
        if session.attempt_count >= crud_auth.VERIFICATION_MAX_ATTEMPTS:
            raise RateLimitError(
                "AUTH_RATE_LIMITED",
                "入力試行回数が上限を超えたか、再送信クールダウン中です。しばらくしてから再試行してください。",
            )
        raise BadRequestError("AUTH_INVALID_INPUT", "認証コードが一致しないか、有効期限が切れています。")

    reset_token = crud_auth.create_reset_token(db, session)

    return SuccessResponse(
        data=VerifyEmailResponseData(verified=True, reset_token=reset_token),
    )
