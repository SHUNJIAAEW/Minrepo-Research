import csv
import os
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UnitResult, MachineResult


REPORT_DIR = Path("reports")


async def generate_csv(store_id: int, record_date: date, db: AsyncSession) -> str:
    """台番データのCSVを生成してパスを返す"""
    REPORT_DIR.mkdir(exist_ok=True)
    filename = REPORT_DIR / f"store{store_id}_{record_date.isoformat()}.csv"

    units = (await db.execute(
        select(UnitResult)
        .where(UnitResult.store_id == store_id, UnitResult.record_date == record_date)
        .order_by(UnitResult.machine_name, UnitResult.unit_number)
    )).scalars().all()

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["台番", "機種名", "ゲーム数", "差枚", "BB回数", "RB回数", "合成確率", "BB確率", "RB確率"])
        for u in units:
            writer.writerow([
                u.unit_number, u.machine_name, u.games, u.diff_medals,
                u.bb_count, u.rb_count, u.combined_prob, u.bb_prob, u.rb_prob,
            ])

    return str(filename)
