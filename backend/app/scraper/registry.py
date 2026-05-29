from .base import BaseScraper
from .minnrepo import MinnrepoScraper

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "みんレポ": MinnrepoScraper,
    # "ホールナビ": HallnaviScraper,  # 追加実装時に登録
}


def get_scraper(site_name: str) -> BaseScraper:
    cls = SCRAPER_REGISTRY.get(site_name)
    if cls is None:
        raise ValueError(f"No scraper registered for site: {site_name}")
    return cls()
