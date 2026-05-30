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


def _summarize(units: list[UnitLike]) -> dict:
    """
    欠損値(None)は平均・勝率の母数から除外する。
    - total_units: 設置台数（全件）
    - 平均/勝率: 値が取得できた台のみを母数にする（未取得台を0扱いして歪めない）
    """
    total_units = len(units)
    diff_units = [u for u in units if u.diff_medals is not None]
    game_units = [u for u in units if u.games is not None]

    total_diff = sum(u.diff_medals for u in diff_units)
    plus_count = sum(1 for u in diff_units if u.diff_medals > 0)

    avg_diff = round(total_diff / len(diff_units), 1) if diff_units else 0.0
    avg_games = round(sum(u.games for u in game_units) / len(game_units), 1) if game_units else 0.0
    win_rate = round(plus_count / len(diff_units), 4) if diff_units else 0.0

    return {
        "total_units": total_units,
        "total_diff_medals": total_diff,
        "avg_diff_medals": avg_diff,
        "avg_games": avg_games,
        "win_rate": win_rate,
        "plus_unit_count": plus_count,
    }


def analyze_units(units: list[UnitLike]) -> AnalysisSummary:
    if not units:
        raise ValueError("No unit data to analyze")

    overall = _summarize(units)

    machine_map: dict[str, list] = {}
    for u in units:
        machine_map.setdefault(u.machine_name, []).append(u)

    machine_summaries: list[MachineSummary] = []
    for name, m_units in machine_map.items():
        s = _summarize(m_units)
        machine_summaries.append(MachineSummary(
            machine_name=name,
            total_units=s["total_units"],
            total_diff_medals=s["total_diff_medals"],
            avg_diff_medals=s["avg_diff_medals"],
            avg_games=s["avg_games"],
            win_rate=s["win_rate"],
            plus_unit_ratio=s["win_rate"],
        ))

    machine_summaries.sort(key=lambda x: x.total_diff_medals, reverse=True)
    top_machine = machine_summaries[0].machine_name if machine_summaries else None

    return AnalysisSummary(
        total_units=overall["total_units"],
        total_diff_medals=overall["total_diff_medals"],
        avg_diff_medals=overall["avg_diff_medals"],
        avg_games=overall["avg_games"],
        win_rate=overall["win_rate"],
        plus_unit_count=overall["plus_unit_count"],
        plus_unit_ratio=overall["win_rate"],
        top_machine=top_machine,
        machine_summaries=machine_summaries,
    )
