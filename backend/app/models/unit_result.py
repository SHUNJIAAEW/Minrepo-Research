from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from .mixins import TimestampMixin


class UnitResult(Base, TimestampMixin):
    """台番別実績"""
    __tablename__ = "unit_results"
    __table_args__ = (
        UniqueConstraint("store_id", "record_date", "unit_number", name="uq_unit_store_date_no"),
        Index("ix_unit_store_date", "store_id", "record_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    machine_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_number: Mapped[int] = mapped_column(Integer, nullable=False)

    games: Mapped[int] = mapped_column(Integer, nullable=True)
    diff_medals: Mapped[int] = mapped_column(Integer, nullable=True)   # 差枚
    bb_count: Mapped[int] = mapped_column(Integer, nullable=True)
    rb_count: Mapped[int] = mapped_column(Integer, nullable=True)
    combined_prob: Mapped[float] = mapped_column(Float, nullable=True)  # 合成確率
    bb_prob: Mapped[float] = mapped_column(Float, nullable=True)
    rb_prob: Mapped[float] = mapped_column(Float, nullable=True)

    store: Mapped["Store"] = relationship(back_populates="unit_results")
