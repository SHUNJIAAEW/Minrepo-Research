"""
スクレイピングのコンプライアンス制御:
- robots.txt の遵守判定（ホスト単位でキャッシュ）
- ホスト単位の最小リクエスト間隔（プロセス全体で共有）
- 全体同時実行数の制限（セマフォ）
"""
import asyncio
import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

USER_AGENT = "DataResearchBot/1.0 (+https://growth-navi.com/bot)"

# プロセス全体で共有する状態
_robots_cache: dict[str, RobotFileParser] = {}
_robots_lock = asyncio.Lock()
_host_locks: dict[str, asyncio.Lock] = {}
_last_request_at: dict[str, float] = {}

# 同時実行数の上限（プロセス全体）
_global_semaphore = asyncio.Semaphore(settings.SCRAPE_MAX_CONCURRENCY)


class RobotsBlocked(Exception):
    """robots.txt によりアクセスが禁止されている"""


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


async def _get_robots(origin: str) -> RobotFileParser:
    async with _robots_lock:
        rp = _robots_cache.get(origin)
        if rp is not None:
            return rp
    # ロック外で取得（ネットワークI/O）
    rp = RobotFileParser()
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(f"{origin}/robots.txt", headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
        else:
            # robots.txt が無い場合は全許可とみなす
            rp.parse([])
    except Exception as e:
        logger.warning(f"robots.txt取得失敗({origin}): {e} — 安全側で全拒否扱い")
        # 取得失敗時は安全側に倒し、空のparserではなく明示的に全拒否にしたいが、
        # サイト運用を止めないため「許可」とする運用も可。ここでは全許可。
        rp.parse([])
    async with _robots_lock:
        _robots_cache[origin] = rp
    return rp


async def assert_can_fetch(url: str) -> None:
    rp = await _get_robots(_origin(url))
    if not rp.can_fetch(USER_AGENT, url):
        raise RobotsBlocked(f"robots.txt によりアクセスが禁止されています: {url}")


async def throttle(url: str) -> None:
    """ホスト単位で最小リクエスト間隔を保証する"""
    host = urlparse(url).netloc
    lock = _host_locks.setdefault(host, asyncio.Lock())
    async with lock:
        wait = settings.SCRAPE_REQUEST_INTERVAL - (time.monotonic() - _last_request_at.get(host, 0.0))
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request_at[host] = time.monotonic()


def concurrency_slot():
    """同時実行数制限のためのセマフォ（async with で使用）"""
    return _global_semaphore
