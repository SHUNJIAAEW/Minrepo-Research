from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from .mixins import TimestampMixin


class MachineResult(Base, TimestampMixin):
    """機種別実績（集計）"""
    __tablename__ = "machine_results"
    __table_args__ = (
        UniqueConstraint("store_id", "record_date", "machine_name", name="uq_machine_store_date_name"),
        Index("ix_machine_store_date", "store_id", "record_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    machine_name: Mapped[str] = mapped_column(String(200), nullable=False)

    total_units: Mapped[int] = mapped_column(Integer, nullable=True)
    total_games: Mapped[int] = mapped_column(Integer, nullable=True)
    total_diff_medals: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_diff_medals: Mapped[float] = mapped_column(Float, nullable=True)
    avg_games: Mapped[float] = mapped_column(Float, nullable=True)
    win_rate: Mapped[float] = mapped_column(Float, nullable=True)         # 勝率
    plus_unit_ratio: Mapped[float] = mapped_column(Float, nullable=True)  # プラス台割合

    store: Mapped["Store"] = relationship(back_populates="machine_results")
