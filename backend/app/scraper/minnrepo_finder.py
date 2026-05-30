"""
みんレポ店舗検索ユーティリティ
店舗名でサイトを検索し、最新レポートURLを返す。
"""
import logging
import urllib.parse
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_URL = "https://min-repo.com/"


class MinnrepoFinder(BaseScraper):
    SITE_NAME = "みんレポ"

    async def find_latest_report_url(self, store_name: str) -> str | None:
        """
        ホール名で検索して最新レポートのURLを返す。
        DataSource.url はレポートIDではなく、この関数で毎回動的に取得する。
        """
        query = urllib.parse.urlencode({"s": store_name})
        search_url = f"{SEARCH_URL}?{query}"
        html = await self.fetch(search_url)
        soup = BeautifulSoup(html, "html.parser")

        # 検索結果の最初のレポートリンク（/数字/ 形式）を取得
        for a in soup.select("a[href]"):
            href = a["href"]
            if href.startswith("https://min-repo.com/") and href.rstrip("/").split("/")[-1].isdigit():
                logger.info(f"Found report for '{store_name}': {href}")
                return href.rstrip("/") + "/"

        logger.warning(f"No report found for store: {store_name}")
        return None
