"""手動トリガー用エンドポイント（開発・デバッグ用）"""
from datetime import date
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.batch.jobs import collect_store, analyze_and_deliver_job
from app.db.base import AsyncSessionLocal

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/collect/{store_id}")
async def trigger_collect(store_id: int, record_date: date, bg: BackgroundTasks):
    async def job():
        async with AsyncSessionLocal() as db:
            await collect_store(store_id, record_date, db)

    bg.add_task(job)
    return {"status": "queued", "store_id": store_id, "record_date": record_date}


@router.post("/analyze")
async def trigger_analyze(record_date: date, bg: BackgroundTasks):
    bg.add_task(analyze_and_deliver_job, record_date)
    return {"status": "queued", "record_date": record_date}
