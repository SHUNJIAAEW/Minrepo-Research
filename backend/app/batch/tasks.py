import asyncio
import logging
from datetime import date, timedelta

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery("pdata", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

celery_app.conf.beat_schedule = {
    # 毎日 03:00 に Hermes 日次フロー（収集→分析→配信）を一括実行
    "hermes-daily": {
        "task": "app.batch.tasks.hermes_daily",
        "schedule": crontab(hour=3, minute=0),
    },
}
celery_app.conf.timezone = "Asia/Tokyo"


def run_async(coro):
    # Celeryワーカー(同期プロセス)からasyncジョブを実行。
    # get_event_loop()はPython3.12+で非推奨/エラーになるため asyncio.run を使う。
    return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=3)
def hermes_daily(self):
    """
    Hermes Agent 日次フローのスケジュール起動。
    Celery Beat は「定時にHermesを起こす」役割に徹し、
    収集・分析・配信・リトライ・通知・ログ記録は orchestrator が担う。
    """
    from app.hermes.orchestrator import run_daily_flow
    try:
        return run_async(run_daily_flow(date.today() - timedelta(days=1), trigger="cron"))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
