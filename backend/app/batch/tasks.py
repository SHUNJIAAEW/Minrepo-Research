import asyncio
import logging
from datetime import date, timedelta

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery("pdata", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

celery_app.conf.beat_schedule = {
    # 毎日 02:00 にデータ取得
    "daily-collect": {
        "task": "app.batch.tasks.collect_all_stores",
        "schedule": crontab(hour=2, minute=0),
    },
    # 毎日 06:00 に分析・レポート配信
    "daily-report": {
        "task": "app.batch.tasks.analyze_and_deliver_all",
        "schedule": crontab(hour=6, minute=0),
    },
}
celery_app.conf.timezone = "Asia/Tokyo"


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3)
def collect_all_stores(self):
    """全アクティブ店舗のデータ収集"""
    from app.batch.jobs import collect_all_stores_job
    try:
        run_async(collect_all_stores_job(date.today() - timedelta(days=1)))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def analyze_and_deliver_all(self):
    """全店舗の分析・配信"""
    from app.batch.jobs import analyze_and_deliver_job
    try:
        run_async(analyze_and_deliver_job(date.today() - timedelta(days=1)))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
