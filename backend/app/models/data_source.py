from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from .mixins import TimestampMixin


class DataSource(Base, TimestampMixin):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    site_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. みんレポ, ホールナビ
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    store: Mapped["Store"] = relationship(back_populates="data_sources")
