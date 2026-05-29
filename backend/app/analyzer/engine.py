from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UnitResult, MachineResult, DailyReport
from app.analyzer.compute import analyze_units, AnalysisSummary


@dataclass
class AnalysisResult:
    store_id: int
    record_date: date
    total_units: int
    total_diff_medals: int
    avg_diff_medals: float
    avg_games: float
    win_rate: float
    plus_unit_count: int
    plus_unit_ratio: float
    top_machine: Optional[str]
    machine_summaries: list[dict]


def _summary_to_result(store_id: int, record_date: date, s: AnalysisSummary) -> AnalysisResult:
    return AnalysisResult(
        store_id=store_id,
        record_date=record_date,
        total_units=s.total_units,
        total_diff_medals=s.total_diff_medals,
        avg_diff_medals=s.avg_diff_medals,
        avg_games=s.avg_games,
        win_rate=s.win_rate,
        plus_unit_count=s.plus_unit_count,
        plus_unit_ratio=s.plus_unit_ratio,
        top_machine=s.top_machine,
        machine_summaries=[ms.__dict__ for ms in s.machine_summaries],
    )


async def run_analysis(store_id: int, record_date: date, db: AsyncSession) -> AnalysisResult:
    """DB上の台番データから日次分析を実行し MachineResult / DailyReport を保存"""
    rows = (await db.execute(
        select(UnitResult).where(
            UnitResult.store_id == store_id,
            UnitResult.record_date == record_date,
        )
    )).scalars().all()

    if not rows:
        raise ValueError(f"No unit data for store={store_id} date={record_date}")

    summary = analyze_units(rows)

    for ms in summary.machine_summaries:
        db.add(MachineResult(store_id=store_id, record_date=record_date, **ms.__dict__))

    db.add(DailyReport(
        store_id=store_id,
        record_date=record_date,
        total_diff_medals=summary.total_diff_medals,
        avg_diff_medals=summary.avg_diff_medals,
        avg_games=summary.avg_games,
        win_rate=summary.win_rate,
        total_units=summary.total_units,
        plus_unit_count=summary.plus_unit_count,
        top_machine=summary.top_machine,
        status="done",
    ))
    await db.commit()

    return _summary_to_result(store_id, record_date, summary)
