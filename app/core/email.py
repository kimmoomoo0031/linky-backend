import logging

logger = logging.getLogger(__name__)


async def send_verification_email(email: str, code: str) -> None:
    # TODO: Resend API 連動
    logger.info("=== 認証コード送信 === to=%s code=%s", email, code)


async def send_password_reset_email(email: str, reset_token: str) -> None:
    # TODO: Resend API 連動
    logger.info("=== パスワードリセット送信 === to=%s token=%s", email, reset_token)
