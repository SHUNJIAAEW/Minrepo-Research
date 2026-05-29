"""
純粋計算ロジック（DB非依存）
台データのリストから分析サマリーを算出する。オンデマンドリサーチ・バッチ両方から利用。
"""
from dataclasses import dataclass, field
from typing import Protocol, Optional


class UnitLike(Protocol):
    machine_name: str
    unit_number: int
    games: Optional[int]
    diff_medals: Optional[int]


@dataclass
class MachineSummary:
    machine_name: str
    total_units: int
    total_diff_medals: int
    avg_diff_medals: float
    avg_games: float
    win_rate: float
    plus_unit_ratio: float


@dataclass
class AnalysisSummary:
    total_units: int
    total_diff_medals: int
    avg_diff_medals: float
    avg_games: float
    win_rate: float
    plus_unit_count: int
    plus_unit_ratio: float
    top_machine: Optional[str]
    machine_summaries: list[MachineSummary] = field(default_factory=list)


def analyze_units(units: list[UnitLike]) -> AnalysisSummary:
    if not units:
        raise ValueError("No unit data to analyze")

    total_units = len(units)
    plus_units = [u for u in units if (u.diff_medals or 0) > 0]
    total_diff = sum(u.diff_medals or 0 for u in units)
    total_games = sum(u.games or 0 for u in units)
    avg_diff = total_diff / total_units
    avg_games = total_games / total_units
    win_rate = len(plus_units) / total_units

    machine_map: dict[str, list] = {}
    for u in units:
        machine_map.setdefault(u.machine_name, []).append(u)

    machine_summaries: list[MachineSummary] = []
    for name, m_units in machine_map.items():
        m_total = sum(u.diff_medals or 0 for u in m_units)
        m_plus = len([u for u in m_units if (u.diff_medals or 0) > 0])
        m_win = m_plus / len(m_units)
        machine_summaries.append(MachineSummary(
            machine_name=name,
            total_units=len(m_units),
            total_diff_medals=m_total,
            avg_diff_medals=round(m_total / len(m_units), 1),
            avg_games=round(sum(u.games or 0 for u in m_units) / len(m_units), 1),
            win_rate=round(m_win, 4),
            plus_unit_ratio=round(m_win, 4),
        ))

    machine_summaries.sort(key=lambda x: x.total_diff_medals, reverse=True)
    top_machine = machine_summaries[0].machine_name if machine_summaries else None

    return AnalysisSummary(
        total_units=total_units,
        total_diff_medals=total_diff,
        avg_diff_medals=round(avg_diff, 1),
        avg_games=round(avg_games, 1),
        win_rate=round(win_rate, 4),
        plus_unit_count=len(plus_units),
        plus_unit_ratio=round(win_rate, 4),
        top_machine=top_machine,
        machine_summaries=machine_summaries,
    )
