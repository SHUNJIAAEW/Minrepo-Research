from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator

from app.scraper.sources import ALLOWED_SOURCES, is_allowed_host, InvalidSourceUrl
from urllib.parse import urlparse


class StoreCreate(BaseModel):
    name: str
    region: Optional[str] = None
    is_active: bool = True


class StoreRead(StoreCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DataSourceCreate(BaseModel):
    site_name: str
    url: str
    is_active: bool = True

    @field_validator("site_name")
    @classmethod
    def known_site(cls, v: str) -> str:
        if v not in ALLOWED_SOURCES:
            raise ValueError(f"未対応の媒体です: {v}")
        return v

    @model_validator(mode="after")
    def validate_url_host(self):
        # SSRF対策: httpsかつ許可ホストのみ受け付ける
        u = urlparse(self.url.strip())
        if u.scheme != "https":
            raise ValueError("URLはhttpsである必要があります")
        if not is_allowed_host(u.hostname, self.site_name):
            raise ValueError(f"許可されていないホストです: {u.hostname}")
        return self
