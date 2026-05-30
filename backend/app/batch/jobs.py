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
    start = time.monotonic()
    # 再収集時の二重計上を防ぐため、同一 store/date の既存台データを削除してから収集
    await db.execute(delete(UnitResult).where(
        UnitResult.store_id == store_id,
        UnitResult.record_date == record_date,
    ))

    sources = (await db.execute(
        select(DataSource).where(
            DataSource.store_id == store_id,
            DataSource.is_active == True,
        )
    )).scalars().all()

    units_collected = 0
    for source in sources:
        try:
            scraper = get_scraper(source.site_name)
            async with scraper:
                url = await _resolve_url(scraper, source)
                if not url:
                    logger.warning(f"Could not resolve URL for source={source.id}")
                    continue
                result = await scraper.scrape_with_retry(store_id, url, record_date)

            if result.success:
                for u in result.units:
                    db.add(UnitResult(
                        store_id=store_id,
                        record_date=record_date,
                        machine_name=u.machine_name,
                        unit_number=u.unit_number,
                        games=u.games,
                        diff_medals=u.diff_medals,
                        bb_count=u.bb_count,
                        rb_count=u.rb_count,
                        combined_prob=u.combined_prob,
                        bb_prob=u.bb_prob,
                        rb_prob=u.rb_prob,
                    ))
                units_collected += len(result.units)
            else:
                db.add(ErrorLog(
                    store_id=store_id,
                    source="scraper",
                    error_type="ScrapeError",
                    message=result.error_message or "Unknown error",
                ))
        except Exception as e:
            logger.exception(f"Scrape failed store={store_id}")
            db.add(ErrorLog(store_id=store_id, source="scraper", error_type=type(e).__name__, message=str(e)))

    elapsed = int(time.monotonic() - start)
    db.add(CollectionLog(
        store_id=store_id,
        record_date=record_date,
        status="success" if units_collected > 0 else "error",
        units_collected=units_collected,
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
