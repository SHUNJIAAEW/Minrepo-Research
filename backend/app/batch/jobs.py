import logging
import time
from datetime import date

from sqlalchemy import select, delete

from app.db.base import AsyncSessionLocal
from app.models import Store, DataSource, UnitResult, CollectionLog, ErrorLog
from app.scraper.registry import get_scraper
from app.analyzer.engine import run_analysis
from app.reporter.csv_reporter import generate_csv
from app.reporter.text_reporter import build_report_text
from app.notifier.dispatcher import dispatch

logger = logging.getLogger(__name__)


async def collect_all_stores_job(record_date: date) -> None:
    async with AsyncSessionLocal() as db:
        stores = (await db.execute(
            select(Store).where(Store.is_active == True)
        )).scalars().all()

        for store in stores:
            await collect_store(store.id, record_date, db)


async def collect_store(store_id: int, record_date: date, db) -> None:
    """
    収集方針（データ保全）:
      1. 先に全取得元をスクレイピングしてメモリに集める（外部I/O）
      2. 取得できた場合のみ、既存データを削除して新データに置換（短いDBトランザクション）
      3. 1件も取れなかった場合は既存データを消さず error ログのみ残す
    これにより収集失敗で前回の正常スナップショットが消えるのを防ぐ。
    """
    start = time.monotonic()

    sources = (await db.execute(
        select(DataSource).where(
            DataSource.store_id == store_id,
            DataSource.is_active == True,
        )
    )).scalars().all()

    collected_units = []   # 取得できた UnitData をためる
    errors: list[str] = []

    for source in sources:
        try:
            scraper = get_scraper(source.site_name)
            async with scraper:
                url = await _resolve_url(scraper, source)
                if not url:
                    errors.append(f"source={source.id}: URL未解決")
                    continue
                result = await scraper.scrape_with_retry(store_id, url, record_date)

            if result.success and result.units:
                collected_units.extend(result.units)
            else:
                errors.append(f"source={source.id}: {result.error_message or '0件'}")
        except Exception as e:
            logger.exception(f"Scrape failed store={store_id}")
            errors.append(f"source={source.id}: {type(e).__name__}: {e}")

    elapsed = int(time.monotonic() - start)

    if collected_units:
        # 取得成功時のみ置換（再収集の二重計上を防ぐ delete-then-insert）
        await db.execute(delete(UnitResult).where(
            UnitResult.store_id == store_id,
            UnitResult.record_date == record_date,
        ))
        for u in collected_units:
            db.add(UnitResult(
                store_id=store_id, record_date=record_date,
                machine_name=u.machine_name, unit_number=u.unit_number,
                games=u.games, diff_medals=u.diff_medals,
                bb_count=u.bb_count, rb_count=u.rb_count,
                combined_prob=u.combined_prob, bb_prob=u.bb_prob, rb_prob=u.rb_prob,
            ))
        status = "success" if not errors else "partial"
    else:
        # 1件も取れていない → 既存データは保持し、エラーのみ記録
        status = "error"

    if errors:
        db.add(ErrorLog(
            store_id=store_id, source="scraper", error_type="ScrapeError",
            message="; ".join(errors)[:2000],
        ))

    db.add(CollectionLog(
        store_id=store_id,
        record_date=record_date,
        status=status,
        units_collected=len(collected_units),
        duration_seconds=elapsed,
    ))
    await db.commit()


async def _resolve_url(scraper, source) -> str | None:
    """
    DataSource.url がレポートID直URLなら使用。
    /tag/ 形式（店舗タグURL）ならみんレポ検索で最新レポートURLを解決する。
    """
    from app.scraper.minnrepo_finder import MinnrepoFinder
    url = source.url
    # レポートIDが直接指定されている場合（例: https://min-repo.com/3132225/）
    if url.rstrip("/").split("/")[-1].isdigit():
        return url
    # タグURLの場合は最新レポートを動的に検索
    if source.site_name == "みんレポ" and "/tag/" in url:
        store_name = url.rstrip("/").split("/")[-1]
        import urllib.parse
        store_name = urllib.parse.unquote(store_name)
        async with MinnrepoFinder() as finder:
            return await finder.find_latest_report_url(store_name)
    return url


async def analyze_and_deliver_job(record_date: date) -> None:
    async with AsyncSessionLocal() as db:
        stores = (await db.execute(
            select(Store).where(Store.is_active == True)
        )).scalars().all()

        for store in stores:
            try:
                result = await run_analysis(store.id, record_date, db)
                csv_path = await generate_csv(store.id, record_date, db)
                message = build_report_text(result, store.name)
                message += f"\n\n📎 CSV: {csv_path}"
                await dispatch(store.id, message, db)
            except Exception as e:
                logger.exception(f"Analyze/deliver failed store={store.id}")
                db.add(ErrorLog(store_id=store.id, source="analyzer", error_type=type(e).__name__, message=str(e)))
                await db.commit()
