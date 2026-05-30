"""
Hermes Agent オーケストレーター（自前の本番運用エージェント本体）。

仕様書の日次実行フローを実装:
  1.スケジューラ起動 → 2.対象店舗取得 → 3.データ収集 → 4.HTML解析(=収集内)
  → 5.整形/6.DB保存(=収集内) → 7.分析 → 8.レポート生成(=分析内) → 9.配信 → 10.ログ保存

特徴:
- ステップ単位で結果を記録し HermesRun に永続化（監視・再実行の起点）
- 店舗単位の失敗は握りつぶさず partial として継続
- 実行終了時、失敗があれば管理者へアラート通知
"""
import logging
import time
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models import Store, HermesRun
from app.hermes import tools
from app.hermes.types import StepResult
from app.notifier.admin import notify_admin

logger = logging.getLogger(__name__)


async def run_daily_flow(record_date: date, trigger: str = "cron") -> dict:
    """全アクティブ店舗に対して 収集→分析→配信 を実行し、実行記録を返す。"""
    started = time.monotonic()
    steps: list[StepResult] = []
    metrics = {
        "stores_total": 0, "collected_ok": 0, "analyzed_ok": 0,
        "delivered_ok": 0, "store_failures": 0,
    }
    errors: list[str] = []

    # 実行レコードを作成（running）
    async with AsyncSessionLocal() as db:
        run = HermesRun(flow="daily", record_date=record_date, trigger=trigger, status="running")
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_id = run.id

    status = "failed"
    try:
        # 1. ヘルスチェック
        health = await tools.tool_health()
        steps.append(StepResult("health", "success" if health.ok else "failed", health.detail or health.error or ""))
        if not health.ok:
            errors.append(f"health: {health.error}")

        # 2. 対象店舗取得
        async with AsyncSessionLocal() as db:
            stores = (await db.execute(select(Store).where(Store.is_active == True))).scalars().all()
            store_list = [(s.id, s.name) for s in stores]
        metrics["stores_total"] = len(store_list)
        steps.append(StepResult("fetch_stores", "success", f"{len(store_list)}店舗"))

        # 3-10. 店舗ごとに 収集→分析→配信
        for store_id, store_name in store_list:
            store_ok = True

            c = await tools.tool_collect(store_id, record_date)
            if c.ok:
                metrics["collected_ok"] += 1
            else:
                errors.append(f"[{store_name}] collect: {c.error or c.detail}")
                # 収集失敗なら分析・配信はスキップ
                steps.append(StepResult(f"store:{store_name}", "failed", f"collect失敗: {c.error or c.detail}"))
                metrics["store_failures"] += 1
                continue

            a = await tools.tool_analyze(store_id, record_date)
            if a.ok:
                metrics["analyzed_ok"] += 1
            else:
                store_ok = False
                errors.append(f"[{store_name}] analyze: {a.error}")

            if a.ok:
                d = await tools.tool_deliver(store_id, record_date)
                if d.ok:
                    metrics["delivered_ok"] += 1
                else:
                    store_ok = False
                    errors.append(f"[{store_name}] deliver: {d.error}")

            if not store_ok:
                metrics["store_failures"] += 1
            steps.append(StepResult(
                f"store:{store_name}",
                "success" if store_ok else "partial",
                f"collect={c.ok} analyze={a.ok}",
            ))

        # 状態サマリー
        st = await tools.tool_status(record_date)
        steps.append(StepResult("status", "success" if st.ok else "failed", st.detail or ""))

        # 実行結果の判定
        if metrics["store_failures"] == 0 and not errors:
            status = "success"
        elif metrics["delivered_ok"] > 0 or metrics["collected_ok"] > 0:
            status = "partial"
        else:
            status = "failed"
    except Exception as e:
        # 予期しない例外でも running を残さない
        logger.exception(f"Hermes daily flow crashed run={run_id}")
        status = "failed"
        errors.append(f"orchestrator: {type(e).__name__}: {e}")
        steps.append(StepResult("orchestrator", "failed", str(e)))
    finally:
        duration = int(time.monotonic() - started)
        error_summary = "\n".join(errors[:50]) if errors else None
        try:
            async with AsyncSessionLocal() as db:
                run = await db.get(HermesRun, run_id)
                if run is not None:
                    run.status = status
                    run.finished_at = datetime.now(timezone.utc)
                    run.duration_seconds = duration
                    run.steps = [s.to_dict() for s in steps]
                    run.metrics = metrics
                    run.error_summary = error_summary
                    await db.commit()
        except Exception:
            logger.exception(f"Failed to finalize HermesRun run={run_id}")

    # 失敗時アラート
    if status != "success":
        await notify_admin(
            f"⚠️ Hermes日次フロー {status.upper()} ({record_date})\n"
            f"店舗 {metrics['delivered_ok']}/{metrics['stores_total']} 配信完了 / "
            f"失敗 {metrics['store_failures']}件\n"
            + (f"\n{error_summary}" if error_summary else "")
        )

    logger.info(f"Hermes daily flow done: run={run_id} status={status} {metrics}")
    return {"run_id": run_id, "status": status, "metrics": metrics, "duration_seconds": duration}
