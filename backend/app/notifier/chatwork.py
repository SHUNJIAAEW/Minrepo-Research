import httpx
import logging

logger = logging.getLogger(__name__)

CHATWORK_API_BASE = "https://api.chatwork.com/v2"


async def send_message(api_token: str, room_id: str, message: str) -> bool:
    headers = {"X-ChatWorkToken": api_token}
    url = f"{CHATWORK_API_BASE}/rooms/{room_id}/messages"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, data={"body": message})
    if resp.status_code != 200:
        logger.error(f"Chatwork send failed: {resp.status_code} {resp.text}")
        return False
    return True
