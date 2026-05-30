"""
データ取得元のホワイトリストとURL検証（SSRF対策）。
許可された媒体・ホスト以外へのアクセスを防ぐ。
"""
from urllib.parse import urlparse

# サイト名 -> 許可ホスト集合
ALLOWED_SOURCES: dict[str, set[str]] = {
    "みんレポ": {"min-repo.com"},
    # "ホールナビ": {"hall-navi.example"},  # 実装時に追加
}

ALLOWED_HOSTS: set[str] = {h for hosts in ALLOWED_SOURCES.values() for h in hosts}


class InvalidSourceUrl(ValueError):
    pass


def is_allowed_host(host: str | None, site_name: str | None = None) -> bool:
    if not host:
        return False
    host = host.lower()
    if site_name is not None:
        return host in ALLOWED_SOURCES.get(site_name, set())
    return host in ALLOWED_HOSTS


def validate_source_url(url: str, site_name: str | None = None) -> str:
    """
    httpsかつ許可ホストのURLのみ通す。正規化して返す。
    SSRF（内部IP・メタデータエンドポイント等）への到達を防ぐ。
    """
    u = urlparse(url.strip())
    if u.scheme != "https":
        raise InvalidSourceUrl("URLはhttpsである必要があります")
    if not is_allowed_host(u.hostname, site_name):
        raise InvalidSourceUrl(f"許可されていないホストです: {u.hostname}")
    return u.geturl()


def normalize_minnrepo_report_url(raw: str) -> str:
    """
    みんレポのレポートURLを /{数値ID}/ 形式に正規化。
    クエリ・パストラバーサル・別ホストを排除する。
    """
    u = urlparse(raw.strip())
    if u.scheme != "https" or (u.hostname or "").lower() != "min-repo.com":
        raise InvalidSourceUrl("みんレポ(min-repo.com)のhttps URLを指定してください")
    report_id = u.path.strip("/")
    if not report_id.isdigit():
        raise InvalidSourceUrl("レポートURLは /{数値ID}/ 形式である必要があります")
    return f"https://min-repo.com/{report_id}/"
