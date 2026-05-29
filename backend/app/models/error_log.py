from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from .mixins import TimestampMixin


class ErrorLog(Base, TimestampMixin):
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # scraper/analyzer/notifier/etc
    error_type: Mapped[str] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    resolved: Mapped[bool] = mapped_column(default=False)
