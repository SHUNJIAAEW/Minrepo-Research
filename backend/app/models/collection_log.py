from datetime import date
from sqlalchemy import String, Integer, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from .mixins import TimestampMixin


class CollectionLog(Base, TimestampMixin):
    __tablename__ = "collection_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success/error/partial
    units_collected: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
