from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.crud import crud_lounge
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.lounge import (
    CreateLoungeRequest,
    CreateLoungeResponseData,
    LoungeCardResponseData,
    LoungeDetailResponseData,
    LoungeListResponseData,
    PostListResponseData,
    PostSearchResponseData,
)

router = APIRouter()

MAX_LOUNGES_PER_USER = 5


# ── POST /lounges ──

@router.post("", status_code=201)
def create_lounge(
    body: CreateLoungeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = crud_lounge.count_by_creator(db, current_user.id)
    if count >= MAX_LOUNGES_PER_USER:
        raise ForbiddenError(
            "LOUNGE_CREATION_LIMIT_EXCEEDED",
            "ラウンジは最大5つまで作成できます。",
        )

    existing = crud_lounge.get_by_name_lower(db, body.name)
    if existing:
        raise ConflictError(
            "LOUNGE_NAME_DUPLICATED",
            "このラウンジ名は既に存在しています。",
        )

    lounge = crud_lounge.create_lounge(
        db,
        name=body.name,
        description=body.description,
        creator_id=current_user.id,
    )

    return SuccessResponse(
        data=CreateLoungeResponseData(
            id=lounge.id,
            name=lounge.name,
            created_at=lounge.created_at,
        )
    )


# ── GET /lounges ──

@router.get("")
def get_lounges(db: Session = Depends(get_db)):
    rows = crud_lounge.get_all_with_post_count(db)
    return SuccessResponse(
        data=LoungeListResponseData(
            lounges=[LoungeCardResponseData(**r) for r in rows]
        )
    )


# ── GET /lounges/recent ──

@router.get("/recent")
def get_recent_lounges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = crud_lounge.get_recent_views(db, current_user.id)
    return SuccessResponse(
        data=LoungeListResponseData(
            lounges=[LoungeCardResponseData(total_post_count=0, **r) for r in rows]
        )
    )


# ── DELETE /lounges/recent/{lounge_id} ──

@router.delete("/recent/{lounge_id}", status_code=204)
def delete_recent_lounge(
    lounge_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud_lounge.delete_view(db, current_user.id, lounge_id)
    return Response(status_code=204)


# ── GET /lounges/{lounge_id} ──

@router.get("/{lounge_id}")
def get_lounge_detail(
    lounge_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    detail = crud_lounge.get_detail_with_post_count(db, lounge_id)
    if not detail:
        raise NotFoundError("LOUNGE_NOT_FOUND", "指定されたラウンジが見つかりません。")

    if current_user:
        crud_lounge.upsert_view(db, current_user.id, lounge_id)

    return SuccessResponse(data=LoungeDetailResponseData(**detail))


# ── GET /lounges/{lounge_id}/posts (スタブ: 6段階で実装) ──

@router.get("/{lounge_id}/posts")
def get_lounge_posts(
    lounge_id: int,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    lounge = crud_lounge.get_by_id(db, lounge_id)
    if not lounge:
        raise NotFoundError("LOUNGE_NOT_FOUND", "指定されたラウンジが見つかりません。")

    return SuccessResponse(
        data=PostListResponseData(posts=[], cursor=None, has_next=False)
    )


# ── GET /lounges/{lounge_id}/posts/search (スタブ: 6段階で実装) ──

@router.get("/{lounge_id}/posts/search")
def search_lounge_posts(
    lounge_id: int,
    q: str = Query(..., min_length=1),
    target: str = Query("title"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    lounge = crud_lounge.get_by_id(db, lounge_id)
    if not lounge:
        raise NotFoundError("LOUNGE_NOT_FOUND", "指定されたラウンジが見つかりません。")

    return SuccessResponse(
        data=PostSearchResponseData(posts=[], total_count=0, cursor=None, has_next=False)
    )
