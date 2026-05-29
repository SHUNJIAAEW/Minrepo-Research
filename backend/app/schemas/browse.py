from typing import Optional
from pydantic import BaseModel


class PrefectureGroup(BaseModel):
    region: str
    prefectures: list[str]


class StoreCardOut(BaseModel):
    store_name: str
    prefecture: str
    report_url: str
    report_id: str
    report_label: str
    total_diff: Optional[int] = None
    avg_diff: Optional[int] = None
    hall_id: Optional[str] = None


class StoreListOut(BaseModel):
    prefecture: str
    page: int
    total_pages: int
    stores: list[StoreCardOut]


class ResearchRequest(BaseModel):
    report_url: str


class UnitOut(BaseModel):
    rank: int
    unit_number: int
    machine_name: str
    games: Optional[int]
    diff_medals: Optional[int]


class MachineOut(BaseModel):
    machine_name: str
    total_units: int
    total_diff_medals: int
    avg_diff_medals: float
    avg_games: float
    win_rate: float


class ResearchResult(BaseModel):
    report_url: str
    store_label: str
    total_units: int
    total_diff_medals: int
    avg_diff_medals: float
    avg_games: float
    win_rate: float
    plus_unit_count: int
    top_machine: Optional[str]
    machines: list[MachineOut]
    top_units: list[UnitOut]
