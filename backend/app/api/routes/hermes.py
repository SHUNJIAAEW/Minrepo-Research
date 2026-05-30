"""
Hermes Agent REST トリガー / 監視API。
外部の運用エージェント・スケジューラ・運用者ダッシュボードから叩く。
すべて APIキー(X-API-Key) で保護。
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.core.security import require_api_key
from app.db.base import get_db, AsyncSessionLocal
from app.models import HermesRun
from app.hermes import tools
from app.hermes.orchestrator import run_daily_flow
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/hermes", tags=["hermes"], dependencies=[Depends(require_api_key)])


def _default_date() -> date:
    return date.today() - timedelta(days=1)


class RunDailyRequest(BaseModel):
    record_date: date | None = None
    background: bool = True


@router.post("/run-daily")
async def run_daily(body: RunDailyRequest, bg: BackgroundTasks):
    """日次フローを起動。background=True で即時202、Falseで完了待ち。"""
    rd = body.record_date or _default_date()
    if body.background:
        bg.add_task(run_daily_flow, rd, "api")
        return {"status": "accepted", "record_date": str(rd)}
    result = await run_daily_flow(rd, trigger="api")
    return result


# --- 個別ツール（エージェントが段階的に叩く用） ---
@router.post("/tools/collect")
async def call_collect(store_id: int = Query(...), record_date: date | None = None):
    res = await tools.tool_collect(store_id, record_date or _default_date())
    return res.to_dict()


@router.post("/tools/analyze")
async def call_analyze(store_id: int = Query(...), record_date: date | None = None):
    res = await tools.tool_analyze(store_id, record_date or _default_date())
    return res.to_dict()


@router.post("/tools/deliver")
async def call_deliver(store_id: int = Query(...), record_date: date | None = None):
    res = await tools.tool_deliver(store_id, record_date or _default_date())
    return res.to_dict()


@router.get("/tools/status")
async def call_status(record_date: date | None = None):
    res = await tools.tool_status(record_date or _default_date())
    return res.to_dict()


@router.get("/tools/health")
async def call_health():
    res = await tools.tool_health()
    return res.to_dict()


# --- 監視: 実行履歴 ---
@router.get("/runs")
async def list_runs(limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(HermesRun).order_by(HermesRun.id.desc()).limit(limit)
    )).scalars().all()
    return rows


@router.get("/runs/{run_id}")
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(HermesRun, run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    return run
