import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class UnitData:
    unit_number: int
    machine_name: str
    games: Optional[int] = None
    diff_medals: Optional[int] = None
    bb_count: Optional[int] = None
    rb_count: Optional[int] = None
    combined_prob: Optional[float] = None
    bb_prob: Optional[float] = None
    rb_prob: Optional[float] = None


@dataclass
class ScrapeResult:
    store_id: int
    record_date: date
    units: list[UnitData] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


class BaseScraper(ABC):
    """全スクレイパーの基底クラス"""

    SITE_NAME: str = ""

    def __init__(self):
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (compatible; DataResearchBot/1.0)"
        )
        return self

    async def __aexit__(self, *args):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        await self._playwright.stop()

    async def fetch(self, url: str) -> str:
        """robots.txt遵守・レート制限付きフェッチ"""
        await asyncio.sleep(settings.SCRAPE_REQUEST_INTERVAL)
        page = await self._context.new_page()
        try:
            # networkidle は広告の常時通信で発火しないため domcontentloaded を使用。
            # テーブルはサーバーレンダリングされた初期HTMLに含まれる。
            await page.goto(url, timeout=settings.SCRAPE_TIMEOUT * 1000, wait_until="domcontentloaded")
            return await page.content()
        finally:
            await page.close()

    @abstractmethod
    async def scrape(self, store_id: int, url: str, record_date: date) -> ScrapeResult:
        """サイト固有のスクレイピング実装"""
        ...

    async def scrape_with_retry(self, store_id: int, url: str, record_date: date) -> ScrapeResult:
        last_error = None
        for attempt in range(1, settings.SCRAPE_MAX_RETRIES + 1):
            try:
                result = await self.scrape(store_id, url, record_date)
                if result.success:
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed for store={store_id}: {e}")
                if attempt < settings.SCRAPE_MAX_RETRIES:
                    await asyncio.sleep(settings.SCRAPE_RETRY_INTERVAL)

        return ScrapeResult(
            store_id=store_id,
            record_date=record_date,
            success=False,
            error_message=str(last_error),
        )
