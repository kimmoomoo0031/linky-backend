from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.lounge import Lounge
from app.models.lounge_view import LoungeView
from app.models.post import Post


def get_by_id(db: Session, lounge_id: int) -> Lounge | None:
    return db.query(Lounge).filter(Lounge.id == lounge_id).first()


def get_by_name_lower(db: Session, name: str) -> Lounge | None:
    return db.query(Lounge).filter(func.lower(Lounge.name) == name.lower()).first()


def count_by_creator(db: Session, user_id: int) -> int:
    return db.query(func.count(Lounge.id)).filter(Lounge.creator_id == user_id).scalar() or 0


def create_lounge(db: Session, *, name: str, description: str, creator_id: int) -> Lounge:
    lounge = Lounge(
        name=name,
        description=description,
        creator_id=creator_id,
    )
    db.add(lounge)
    db.flush()
    return lounge


def get_all_with_post_count(db: Session) -> list[dict]:
    """全ラウンジ一覧 + 各ラウンジの投稿数を返す。"""
    rows = (
        db.query(
            Lounge.id,
            Lounge.name,
            Lounge.cover_image_url,
            func.count(Post.id).label("total_post_count"),
        )
        .outerjoin(Post, Post.lounge_id == Lounge.id)
        .group_by(Lounge.id)
        .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "thumbnail_url": r.cover_image_url,
            "total_post_count": r.total_post_count,
        }
        for r in rows
    ]


def get_detail_with_post_count(db: Session, lounge_id: int) -> dict | None:
    """ラウンジ詳細 + 投稿数を返す。"""
    row = (
        db.query(
            Lounge.id,
            Lounge.name,
            Lounge.description,
            Lounge.created_at,
            Lounge.cover_image_url,
            func.count(Post.id).label("total_post_count"),
        )
        .outerjoin(Post, Post.lounge_id == Lounge.id)
        .filter(Lounge.id == lounge_id)
        .group_by(Lounge.id)
        .first()
    )
    if not row:
        return None
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "created_at": row.created_at,
        "total_post_count": row.total_post_count,
        "cover_image_url": row.cover_image_url,
    }


# ── 最近閲覧 ──

def get_recent_views(db: Session, user_id: int, limit: int = 18) -> list[dict]:
    rows = (
        db.query(
            Lounge.id,
            Lounge.name,
            Lounge.cover_image_url,
        )
        .join(LoungeView, LoungeView.lounge_id == Lounge.id)
        .filter(LoungeView.user_id == user_id)
        .order_by(LoungeView.viewed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "thumbnail_url": r.cover_image_url,
        }
        for r in rows
    ]


def upsert_view(db: Session, user_id: int, lounge_id: int) -> None:
    """閲覧履歴を UPSERT する。既存なら viewed_at 更新、なければ INSERT。"""
    existing = (
        db.query(LoungeView)
        .filter(LoungeView.user_id == user_id, LoungeView.lounge_id == lounge_id)
        .first()
    )
    if existing:
        existing.viewed_at = func.now()
    else:
        db.add(LoungeView(user_id=user_id, lounge_id=lounge_id))


def delete_view(db: Session, user_id: int, lounge_id: int) -> None:
    db.query(LoungeView).filter(
        LoungeView.user_id == user_id,
        LoungeView.lounge_id == lounge_id,
    ).delete()
