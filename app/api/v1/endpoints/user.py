from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError
from app.core.security import verify_password
from app.crud import crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import (
    ProfileResponseData,
    UpdateProfileRequest,
    UpdateProfileResponseData,
    WithdrawRequest,
    WithdrawResponseData,
)

router = APIRouter()


# ── GET /users/me/profile ──

@router.get("/me/profile")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return SuccessResponse(
        data=ProfileResponseData(
            id=current_user.id,
            email=current_user.email,
            nickname=current_user.nickname,
            role=current_user.role,
            auth_provider=current_user.auth_provider,
        )
    )


# ── PATCH /users/me/profile ──

@router.patch("/me/profile")
def update_my_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    has_password_fields = any([body.current_password, body.new_password, body.new_password_confirm])

    if has_password_fields and current_user.auth_provider != "local":
        raise ForbiddenError("AUTH_FORBIDDEN", "この操作は許可されていません。")

    if body.nickname is not None:
        existing = crud_user.get_by_nickname(db, body.nickname)
        if existing and existing.id != current_user.id:
            raise ConflictError("AUTH_NICKNAME_DUPLICATED", "このニックネームは既に使用されています。")
        crud_user.update_nickname(db, current_user, body.nickname)

    if has_password_fields:
        if not body.current_password or not body.new_password or not body.new_password_confirm:
            raise BadRequestError(
                "AUTH_INVALID_INPUT",
                "入力値を確認してください。",
                details=[{"field": "current_password", "message": "パスワード変更には全フィールドが必要です。"}],
            )

        if not verify_password(body.current_password, current_user.local_credential.password_hash):
            raise BadRequestError(
                "AUTH_INVALID_INPUT",
                "入力値を確認してください。",
                details=[{"field": "current_password", "message": "現在のパスワードが一致しません。"}],
            )

        if body.new_password != body.new_password_confirm:
            raise BadRequestError(
                "AUTH_INVALID_INPUT",
                "入力値を確認してください。",
                details=[{"field": "new_password_confirm", "message": "パスワードが一致しません。"}],
            )

        crud_user.update_password(db, current_user, body.new_password)

    return SuccessResponse(data=UpdateProfileResponseData())


# ── POST /users/me/withdraw ──

@router.post("/me/withdraw")
def withdraw(
    body: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.auth_provider == "local":
        if not body.current_password:
            raise BadRequestError(
                "AUTH_INVALID_INPUT",
                "入力値を確認してください。",
                details=[{"field": "current_password", "message": "パスワードが必要です。"}],
            )
        if not verify_password(body.current_password, current_user.local_credential.password_hash):
            raise BadRequestError(
                "AUTH_INVALID_INPUT",
                "入力値を確認してください。",
                details=[{"field": "current_password", "message": "現在のパスワードが一致しません。"}],
            )
    else:
        if body.current_password:
            raise ForbiddenError("AUTH_FORBIDDEN", "この操作は許可されていません。")

    reason_text = body.reason_text if body.reason == "other" else None
    crud_user.withdraw_user(db, current_user, body.reason, reason_text)

    return SuccessResponse(data=WithdrawResponseData())
