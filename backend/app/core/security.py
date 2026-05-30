import secrets
from typing import Optional
from fastapi import Header, HTTPException

from app.core.config import settings


async def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    """
    操作系エンドポイント保護用のAPIキー依存。
    ヘッダ欠如・不正のいずれも401を返す（タイミング攻撃を避けるため compare_digest 比較）。
    """
    expected = settings.ADMIN_API_KEY
    if not x_api_key or not expected or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="無効なAPIキーです")
