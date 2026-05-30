from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from .mixins import TimestampMixin


class DailyReport(Base, TimestampMixin):
    __tablename__ = "daily_reports"
    __table_args__ = (
        UniqueConstraint("store_id", "record_date", name="uq_report_store_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)

    total_diff_medals: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_diff_medals: Mapped[float] = mapped_column(Float, nullable=True)
    avg_games: Mapped[float] = mapped_column(Float, nullable=True)
    win_rate: Mapped[float] = mapped_column(Float, nullable=True)
    total_units: Mapped[int] = mapped_column(Integer, nullable=True)
    plus_unit_count: Mapped[int] = mapped_column(Integer, nullable=True)

    top_machine: Mapped[str] = mapped_column(String(200), nullable=True)
    report_text: Mapped[str] = mapped_column(Text, nullable=True)
    csv_path: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/done/error
