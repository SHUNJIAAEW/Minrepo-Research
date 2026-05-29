"""
エリア（都道府県）から店舗を選び、オンデマンドでリサーチするAPI。
WebフロントエンドのSPAから呼び出される。
"""
import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.scraper.minnrepo_browser import MinnrepoBrowser, PREFECTURES, ALL_PREFECTURES
from app.scraper.minnrepo import MinnrepoScraper
from app.analyzer.compute import analyze_units
from app.schemas.browse import (
    PrefectureGroup, StoreListOut, StoreCardOut,
    ResearchRequest, ResearchResult, MachineOut, UnitOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/browse", tags=["browse"])


@router.get("/prefectures", response_model=list[PrefectureGroup])
async def get_prefectures():
    """地方区分ごとの都道府県リスト"""
    return [PrefectureGroup(region=region, prefectures=prefs) for region, prefs in PREFECTURES.items()]


@router.get("/stores", response_model=StoreListOut)
async def list_stores(
    prefecture: str = Query(..., description="都道府県名 例: 愛知県"),
    page: int = Query(1, ge=1),
):
    if prefecture not in ALL_PREFECTURES:
        raise HTTPException(400, f"未対応の都道府県です: {prefecture}")

    try:
        async with MinnrepoBrowser() as browser:
            result = await browser.list_stores(prefecture, page)
    except Exception as e:
        logger.exception("Store listing failed")
        raise HTTPException(502, f"店舗一覧の取得に失敗しました: {e}")

    return StoreListOut(
        prefecture=result.prefecture,
        page=result.page,
        total_pages=result.total_pages,
        stores=[StoreCardOut(**c.__dict__) for c in result.stores],
    )


@router.post("/research", response_model=ResearchResult)
async def research_store(body: ResearchRequest):
    """選択した店舗レポートをその場でスクレイピング・分析して返す"""
    report_url = body.report_url.rstrip("/") + "/"
    if not report_url.startswith("https://min-repo.com/"):
        raise HTTPException(400, "みんレポのレポートURLを指定してください")

    try:
        async with MinnrepoScraper() as scraper:
            scrape = await scraper.scrape_with_retry(store_id=0, url=report_url, record_date=date.today())
    except Exception as e:
        logger.exception("Research scrape failed")
        raise HTTPException(502, f"データ取得に失敗しました: {e}")

    if not scrape.success or not scrape.units:
        raise HTTPException(404, "台データが取得できませんでした")

    summary = analyze_units(scrape.units)

    # 差枚降順 TOP30
    sorted_units = sorted(scrape.units, key=lambda u: (u.diff_medals or 0), reverse=True)
    top_units = [
        UnitOut(
            rank=i,
            unit_number=u.unit_number,
            machine_name=u.machine_name,
            games=u.games,
            diff_medals=u.diff_medals,
        )
        for i, u in enumerate(sorted_units[:30], 1)
    ]

    machines = [
        MachineOut(
            machine_name=m.machine_name,
            total_units=m.total_units,
            total_diff_medals=m.total_diff_medals,
            avg_diff_medals=m.avg_diff_medals,
            avg_games=m.avg_games,
            win_rate=m.win_rate,
        )
        for m in summary.machine_summaries
    ]

    return ResearchResult(
        report_url=report_url,
        store_label=report_url,
        total_units=summary.total_units,
        total_diff_medals=summary.total_diff_medals,
        avg_diff_medals=summary.avg_diff_medals,
        avg_games=summary.avg_games,
        win_rate=summary.win_rate,
        plus_unit_count=summary.plus_unit_count,
        top_machine=summary.top_machine,
        machines=machines,
        top_units=top_units,
    )
