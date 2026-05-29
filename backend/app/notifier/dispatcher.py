import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeliverySetting
from app.core.config import settings
from . import chatwork

logger = logging.getLogger(__name__)


async def dispatch(store_id: int, message: str, db: AsyncSession) -> None:
    """store の配信設定を元に全チャンネルへ送信"""
    settings_rows = (await db.execute(
        select(DeliverySetting).where(
            DeliverySetting.store_id == store_id,
            DeliverySetting.is_active == True,
        )
    )).scalars().all()

    for s in settings_rows:
        try:
            if s.channel == "chatwork":
                await chatwork.send_message(settings.CHATWORK_API_TOKEN, s.destination, message)
            else:
                logger.info(f"Channel '{s.channel}' not implemented yet")
        except Exception as e:
            logger.error(f"Dispatch error store={store_id} channel={s.channel}: {e}")
