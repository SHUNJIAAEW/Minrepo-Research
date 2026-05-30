import re
import logging
from datetime import date

from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapeResult, UnitData

logger = logging.getLogger(__name__)


class MinnrepoScraper(BaseScraper):
    """
    みんレポ用スクレイパー
    URL例: https://min-repo.com/3132225/
    全台データ: https://min-repo.com/3132225/?kishu=all
    """

    SITE_NAME = "みんレポ"

    async def scrape(self, store_id: int, url: str, record_date: date) -> ScrapeResult:
        # ?kishu=all で全台一覧を取得
        all_url = url.rstrip("/") + "/?kishu=all"
        html = await self.fetch(all_url)
        soup = BeautifulSoup(html, "html.parser")

        units = self._parse_unit_table(soup)
        if not units:
            logger.warning(f"No units parsed for store={store_id} url={all_url}")

        return ScrapeResult(store_id=store_id, record_date=record_date, units=units)

    def _parse_unit_table(self, soup: BeautifulSoup) -> list[UnitData]:
        """
        table（クラスなし）: 機種 | 台番 | 差枚 | G数 | 出率
        ヘッダ行は th で構成される。
        """
        table = self._find_unit_table(soup)
        if table is None:
            return []

        # ヘッダ名から列インデックスを特定（列順変更に強くする）
        col = self._column_index(table)

        units = []
        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            try:
                machine_name = cells[col["機種"]].get_text(strip=True)
                unit_number = self._to_int(cells[col["台番"]].get_text())
                diff_medals = self._to_int(cells[col["差枚"]].get_text())
                games = self._to_int(cells[col["G数"]].get_text())
            except (KeyError, IndexError):
                continue

            if not machine_name or unit_number is None:
                continue

            units.append(UnitData(
                unit_number=unit_number,
                machine_name=machine_name,
                games=games,
                diff_medals=diff_medals,
            ))

        return units

    # 全台一覧テーブルが必ず持つヘッダ
    _REQUIRED_HEADERS = {"機種", "台番", "差枚", "G数"}

    def _find_unit_table(self, soup):
        """ヘッダ名に「機種/台番/差枚/G数」を全て含むtableを台データ表として選ぶ"""
        for t in soup.find_all("table"):
            headers = {th.get_text(strip=True) for th in t.select("th")}
            if self._REQUIRED_HEADERS.issubset(headers):
                return t
        return None

    @staticmethod
    def _column_index(table) -> dict[str, int]:
        """ヘッダ行から列名 -> 列インデックスのマップを作る"""
        ths = table.select("tr th")
        idx = {}
        for i, th in enumerate(ths):
            label = th.get_text(strip=True)
            if label and label not in idx:
                idx[label] = i
        return idx

    @staticmethod
    def _to_int(text: str) -> int | None:
        cleaned = re.sub(r"[^\d\-]", "", text.replace(",", ""))
        try:
            return int(cleaned)
        except (ValueError, TypeError):
            return None
