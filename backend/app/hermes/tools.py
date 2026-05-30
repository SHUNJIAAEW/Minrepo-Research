"""
Hermes Agent ツール層。

ここで定義する async 関数群が「エージェントが呼べる操作」の正本。
- 自前オーケストレーター(orchestrator.py)
- REST API(routes/hermes.py)
- CLI(cli.py)
- 将来のLLMエージェント / MCPサーバー
これらすべてがこの層を共通インターフェースとして利用する。

各ツールは ToolResult を返し、例外を握りつぶさず構造化して報告する（冪等・再実行安全）。
"""
import logging
import time
from datetime import date

from sqlalchemy import select, func

from app.db.base import AsyncSessionLocal
from app.models import Store, DailyReport, CollectionLog, ErrorLog
from app.batch.jobs import collect_store, _resolve_url  # 既存ジョブを再利用
from app.analyzer.engine import run_analysis
from app.reporter.csv_reporter import generate_csv
from app.reporter.text_reporter import build_report_text
from app.notifier.dispatcher import dispatch
from app.hermes.types import ToolResult

logger = logging.getLogger(__name__)


async def tool_health() -> ToolResult:
    """DB接続・アクティブ店舗数を確認するヘルスチェック"""
    try:
        async with AsyncSessionLocal() as db:
            active = (await db.execute(
                select(func.count()).select_from(Store).where(Store.is_active == True)
            )).scalar_one()
        return ToolResult(ok=True, tool="health", detail="ok", data={"active_stores": active})
    except Exception as e:
        logger.exception("health check failed")
        return ToolResult(ok=False, tool="health", error=str(e))


async def tool_collect(store_id: int, record_date: date) -> ToolResult:
    """指定店舗のデータ収集（冪等: 既存データは削除して再投入）"""
    start = time.monotonic()
    try:
        async with AsyncSessionLocal() as db:
            await collect_store(store_id, record_date, db)
            log = (await db.execute(
                select(CollectionLog)
                .where(CollectionLog.store_id == store_id, CollectionLog.record_date == record_date)
                .order_by(CollectionLog.id.desc())
            )).scalars().first()
        units = log.units_collected if log else 0
        ok = units > 0
        return ToolResult(
            ok=ok, tool="collect",
            detail=f"store={store_id} units={units}",
            data={"store_id": store_id, "record_date": str(record_date), "units": units},
        )
    except Exception as e:
        logger.exception(f"collect failed store={store_id}")
        return ToolResult(ok=False, tool="collect", error=str(e),
                          data={"store_id": store_id, "record_date": str(record_date)})
    finally:
        logger.info(f"tool_collect store={store_id} took {time.monotonic()-start:.1f}s")


async def tool_analyze(store_id: int, record_date: date) -> ToolResult:
    """収集済み台データを分析し DailyReport/MachineResult を生成"""
    try:
        async with AsyncSessionLocal() as db:
            result = await run_analysis(store_id, record_date, db)
        return ToolResult(
            ok=True, tool="analyze",
            detail=f"store={store_id} 総差枚={result.total_diff_medals:+} 注目={result.top_machine}",
            data={
                "store_id": store_id,
                "total_diff_medals": result.total_diff_medals,
                "avg_diff_medals": result.avg_diff_medals,
                "win_rate": result.win_rate,
                "top_machine": result.top_machine,
            },
        )
    except Exception as e:
        logger.exception(f"analyze failed store={store_id}")
        return ToolResult(ok=False, tool="analyze", error=str(e), data={"store_id": store_id})


async def tool_deliver(store_id: int, record_date: date) -> ToolResult:
    """分析済みレポートをCSV生成・整形して配信先へ送信"""
    try:
        async with AsyncSessionLocal() as db:
            store = await db.get(Store, store_id)
            if store is None:
                return ToolResult(ok=False, tool="deliver", error="store not found",
                                  data={"store_id": store_id})
            report = (await db.execute(
                select(DailyReport).where(
                    DailyReport.store_id == store_id,
                    DailyReport.record_date == record_date,
                )
            )).scalars().first()
            if report is None:
                return ToolResult(ok=False, tool="deliver", error="no analysis report; run analyze first",
                                  data={"store_id": store_id})

            csv_path = await generate_csv(store_id, record_date, db)
            # text_reporter は AnalysisResult を想定するため、最小限の再構築は避け、
            # 既存レポートからメッセージを組む。
            message = _format_report_message(store.name, report)
            message += f"\n\n📎 CSV: {csv_path}"
            await dispatch(store_id, message, db)
        return ToolResult(ok=True, tool="deliver", detail=f"store={store_id} delivered",
                          data={"store_id": store_id, "csv_path": csv_path})
    except Exception as e:
        logger.exception(f"deliver failed store={store_id}")
        return ToolResult(ok=False, tool="deliver", error=str(e), data={"store_id": store_id})


async def tool_status(record_date: date) -> ToolResult:
    """指定日の運用状況サマリー（収集ログ・レポート数・未解決エラー）"""
    try:
        async with AsyncSessionLocal() as db:
            stores_total = (await db.execute(
                select(func.count()).select_from(Store).where(Store.is_active == True)
            )).scalar_one()
            reports = (await db.execute(
                select(func.count()).select_from(DailyReport).where(DailyReport.record_date == record_date)
            )).scalar_one()
            collected = (await db.execute(
                select(func.count(func.distinct(CollectionLog.store_id))).where(
                    CollectionLog.record_date == record_date,
                    CollectionLog.status.in_(["success", "partial"]),
                )
            )).scalar_one()
            unresolved = (await db.execute(
                select(func.count()).select_from(ErrorLog).where(ErrorLog.resolved == False)
            )).scalar_one()
        return ToolResult(
            ok=True, tool="status",
            detail=f"date={record_date} reports={reports}/{stores_total} errors={unresolved}",
            data={
                "record_date": str(record_date),
                "stores_total": stores_total,
                "collected_ok": collected,
                "reports": reports,
                "unresolved_errors": unresolved,
            },
        )
    except Exception as e:
        logger.exception("status failed")
        return ToolResult(ok=False, tool="status", error=str(e))


def _format_report_message(store_name: str, report) -> str:
    wr = (report.win_rate or 0) * 100
    return (
        f"【日次レポート】{store_name}  {report.record_date.isoformat()}\n"
        + "─" * 24 + "\n"
        f"総差枚：{report.total_diff_medals:+,}枚\n"
        f"平均差枚：{report.avg_diff_medals:+,.1f}枚\n"
        f"平均G数：{report.avg_games:,.1f}G\n"
        f"勝率：{wr:.1f}%（プラス{report.plus_unit_count}台 / {report.total_units}台）\n"
        f"注目機種：{report.top_machine or '-'}"
    )


# エージェント/外部から参照するためのツールカタログ
TOOL_CATALOG = {
    "health": {"fn": tool_health, "args": [], "desc": "DB接続とアクティブ店舗数を確認"},
    "collect": {"fn": tool_collect, "args": ["store_id", "record_date"], "desc": "店舗データ収集"},
    "analyze": {"fn": tool_analyze, "args": ["store_id", "record_date"], "desc": "分析・レポート生成"},
    "deliver": {"fn": tool_deliver, "args": ["store_id", "record_date"], "desc": "レポート配信"},
    "status": {"fn": tool_status, "args": ["record_date"], "desc": "運用状況サマリー"},
}
