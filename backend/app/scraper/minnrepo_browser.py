"""
みんレポ エリア（都道府県）ブラウザ
都道府県カテゴリページから店舗カード（最新レポート）を一覧取得する。

カード構造:
  div.ichiran_post
    div.ichiran_title > a  … レポートURL + "5/28(木) 店舗名"
    div.ichiran_result     … "総差枚：+12,200 / 平均差枚：+69"
    div.hall_header
      span.hall_name > a   … タグURL・店舗名
      span.todofuken > a   … 都道府県
    span.fab-btn[data-hallid]
"""
import re
import logging
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

BASE = "https://min-repo.com"

# 都道府県（地方区分つき）
PREFECTURES: dict[str, list[str]] = {
    "北海道・東北": ["北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"],
    "関東": ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"],
    "中部": ["新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県"],
    "近畿": ["三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"],
    "中国・四国": ["鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県"],
    "九州・沖縄": ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"],
}

ALL_PREFECTURES = [p for group in PREFECTURES.values() for p in group]


@dataclass
class StoreCard:
    store_name: str
    prefecture: str
    report_url: str
    report_id: str
    report_label: str            # "5/28(木) 店舗名"
    total_diff: Optional[int] = None
    avg_diff: Optional[int] = None
    hall_id: Optional[str] = None
    tag_url: Optional[str] = None


@dataclass
class StoreListResult:
    prefecture: str
    page: int
    total_pages: int
    stores: list[StoreCard] = field(default_factory=list)


class MinnrepoBrowser(BaseScraper):
    SITE_NAME = "みんレポ"

    def category_url(self, prefecture: str, page: int = 1) -> str:
        enc = urllib.parse.quote(prefecture)
        if page <= 1:
            return f"{BASE}/category/{enc}/"
        return f"{BASE}/category/{enc}/page/{page}/"

    async def list_stores(self, prefecture: str, page: int = 1) -> StoreListResult:
        if prefecture not in ALL_PREFECTURES:
            raise ValueError(f"Unknown prefecture: {prefecture}")

        url = self.category_url(prefecture, page)
        html = await self.fetch(url)
        soup = BeautifulSoup(html, "html.parser")

        stores = [self._parse_card(card) for card in soup.select("div.ichiran_post")]
        stores = [s for s in stores if s]

        total_pages = self._parse_total_pages(soup)

        return StoreListResult(prefecture=prefecture, page=page, total_pages=total_pages, stores=stores)

    def _parse_card(self, card) -> Optional[StoreCard]:
        try:
            title_a = card.select_one("div.ichiran_title a")
            if not title_a:
                return None
            report_url = title_a.get("href", "").rstrip("/") + "/"
            report_label = title_a.get_text(strip=True)
            report_id = report_url.rstrip("/").split("/")[-1]
            if not report_id.isdigit():
                return None

            hall_a = card.select_one("span.hall_name a")
            store_name = hall_a.get_text(strip=True) if hall_a else report_label
            tag_url = hall_a.get("href") if hall_a else None

            pref_a = card.select_one("span.todofuken a")
            prefecture = pref_a.get_text(strip=True) if pref_a else ""

            result_div = card.select_one("div.ichiran_result")
            total_diff, avg_diff = self._parse_result(result_div.get_text() if result_div else "")

            fab = card.select_one("span.fab-btn")
            hall_id = fab.get("data-hallid") if fab else None

            return StoreCard(
                store_name=store_name,
                prefecture=prefecture,
                report_url=report_url,
                report_id=report_id,
                report_label=report_label,
                total_diff=total_diff,
                avg_diff=avg_diff,
                hall_id=hall_id,
                tag_url=tag_url,
            )
        except Exception as e:
            logger.debug(f"Card parse error: {e}")
            return None

    @staticmethod
    def _parse_result(text: str) -> tuple[Optional[int], Optional[int]]:
        # "総差枚：+12,200 / 平均差枚：+69"
        total = avg = None
        m = re.search(r"総差枚[：:]\s*([+\-]?[\d,]+)", text)
        if m:
            total = int(m.group(1).replace(",", ""))
        m = re.search(r"平均差枚[：:]\s*([+\-]?[\d,]+)", text)
        if m:
            avg = int(m.group(1).replace(",", ""))
        return total, avg

    @staticmethod
    def _parse_total_pages(soup) -> int:
        nums = []
        for a in soup.select("nav a, div.pagination a, a.page-numbers"):
            t = a.get_text(strip=True)
            if t.isdigit():
                nums.append(int(t))
        return max(nums) if nums else 1

    async def scrape(self, store_id: int, url: str, record_date):
        """このクラスはブラウズ専用。台データ取得は MinnrepoScraper を使うこと。"""
        raise NotImplementedError("Use MinnrepoScraper for unit-data scraping")
