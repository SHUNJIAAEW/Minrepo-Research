from datetime import datetime
from typing import Optional
from pydantic import BaseModel


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
