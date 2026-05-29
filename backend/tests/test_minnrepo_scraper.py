"""
みんレポスクレイパー 結合テスト
実際のサイトに接続するので CI では skip すること。
実行: pytest tests/test_minnrepo_scraper.py -v -s
"""
import asyncio
from datetime import date
import pytest

from app.scraper.minnrepo import MinnrepoScraper


@pytest.mark.asyncio
async def test_scrape_unit_data():
    url = "https://min-repo.com/3132225/"  # サンプルレポート
    async with MinnrepoScraper() as scraper:
        result = await scraper.scrape(store_id=1, url=url, record_date=date(2026, 5, 28))

    assert result.success, result.error_message
    assert len(result.units) > 0, "台データが取得できない"

    # 最初の台を検証
    u = result.units[0]
    assert u.unit_number is not None
    assert u.machine_name
    assert u.games is not None
    assert u.diff_medals is not None

    print(f"\n取得台数: {len(result.units)}")
    print(f"サンプル: {u.unit_number}番台 {u.machine_name} 差枚={u.diff_medals:+,} G数={u.games:,}")
