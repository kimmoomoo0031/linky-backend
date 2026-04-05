from __future__ import annotations


class AppError(Exception):

    status_code: int = 500

    def __init__(
        self,
        code: str,
        message: str,
        details: list[dict] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


# 入力値が不正な場合
class BadRequestError(AppError):
    status_code = 400


# トークンが無い・無効・期限切れの場合
class UnauthorizedError(AppError):
    status_code = 401


# 認証済みだが権限が無い場合
class ForbiddenError(AppError):
    status_code = 403


# リソースが存在しない場合（投稿・ラウンジ等）
class NotFoundError(AppError):
    status_code = 404


# 重複等の状態競合（メール重複・ニックネーム重複等）
class ConflictError(AppError):
    status_code = 409


# ファイルサイズ超過
class PayloadTooLargeError(AppError):
    status_code = 413


# サポート対象外のメディアタイプ
class UnsupportedMediaError(AppError):
    status_code = 415


# リクエスト回数制限超過
class RateLimitError(AppError):
    status_code = 429


# サーバー内部エラー
class InternalError(AppError):
    status_code = 500


# 外部サービス（ソーシャルログインAPI等）の連携失敗
class UpstreamError(AppError):
    status_code = 502
