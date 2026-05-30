from datetime import datetime, date
from sqlalchemy import String, Integer, Date, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from .mixins import TimestampMixin


class HermesRun(Base, TimestampMixin):
    """
    Hermes Agent の1回の運用実行（日次フロー等）の記録。
    監視・再実行・障害解析の起点になる。
    """
    __tablename__ = "hermes_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    flow: Mapped[str] = mapped_column(String(50), nullable=False)          # daily / collect / analyze ...
    record_date: Mapped[date] = mapped_column(Date, nullable=True)
    trigger: Mapped[str] = mapped_column(String(30), nullable=False)       # cron / api / cli / agent
    status: Mapped[str] = mapped_column(String(20), default="running")     # running / success / partial / failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)

    # ステップごとの結果（[{name, status, detail, duration_seconds}, ...]）
    steps: Mapped[list] = mapped_column(JSON, default=list)
    # 集計メトリクス（stores_total, units_collected, reports_delivered, errors ...）
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    error_summary: Mapped[str] = mapped_column(Text, nullable=True)
