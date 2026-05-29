from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models import DailyReport, MachineResult, UnitResult

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/daily/{store_id}")
async def get_daily_reports(store_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(DailyReport)
        .where(DailyReport.store_id == store_id)
        .order_by(DailyReport.record_date.desc())
        .limit(30)
    )).scalars().all()
    return rows


@router.get("/machines/{store_id}/{record_date}")
async def get_machine_results(store_id: int, record_date: date, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(MachineResult)
        .where(MachineResult.store_id == store_id, MachineResult.record_date == record_date)
        .order_by(MachineResult.total_diff_medals.desc())
    )).scalars().all()
    return rows


@router.get("/units/{store_id}/{record_date}")
async def get_unit_results(store_id: int, record_date: date, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(UnitResult)
        .where(UnitResult.store_id == store_id, UnitResult.record_date == record_date)
        .order_by(UnitResult.diff_medals.desc())
    )).scalars().all()
    return rows
