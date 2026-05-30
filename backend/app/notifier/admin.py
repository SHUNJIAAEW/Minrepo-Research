"""
運用管理者向けの通知（Hermesの障害アラート等）。
店舗向けの dispatcher とは別系統。Slack Webhook を優先し、なければChatwork管理ルーム。
"""
import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def notify_admin(message: str) -> bool:
    """設定済みの管理チャンネルへアラートを送る。未設定ならログのみ。"""
    sent = False
    if settings.SLACK_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(settings.SLACK_WEBHOOK_URL, json={"text": message})
            sent = resp.status_code == 200
        except Exception as e:
            logger.error(f"admin Slack notify failed: {e}")

    if not sent and settings.CHATWORK_API_TOKEN and settings.CHATWORK_ROOM_ID:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"https://api.chatwork.com/v2/rooms/{settings.CHATWORK_ROOM_ID}/messages",
                    headers={"X-ChatWorkToken": settings.CHATWORK_API_TOKEN},
                    data={"body": message},
                )
            sent = resp.status_code == 200
        except Exception as e:
            logger.error(f"admin Chatwork notify failed: {e}")

    if not sent:
        logger.warning(f"[ADMIN ALERT 未配信] {message}")
    return sent
