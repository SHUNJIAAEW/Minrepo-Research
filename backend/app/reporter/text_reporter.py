from app.analyzer.engine import AnalysisResult


def build_report_text(result: AnalysisResult, store_name: str) -> str:
    lines = [
        f"【日次レポート】{store_name}  {result.record_date.isoformat()}",
        "─" * 40,
        f"総台数：{result.total_units}台",
        f"総差枚：{result.total_diff_medals:+,}枚",
        f"平均差枚：{result.avg_diff_medals:+,.1f}枚",
        f"平均G数：{result.avg_games:,.1f}G",
        f"勝率：{result.win_rate * 100:.1f}%（{result.plus_unit_count}台）",
        "",
        "【機種別TOP5】",
    ]

    for i, ms in enumerate(result.machine_summaries[:5], 1):
        lines.append(
            f"{i}. {ms['machine_name']}  "
            f"{ms['total_diff_medals']:+,}枚  "
            f"勝率{ms['win_rate'] * 100:.0f}%  "
            f"({ms['total_units']}台)"
        )

    return "\n".join(lines)
