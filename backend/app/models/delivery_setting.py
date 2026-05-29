from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from .mixins import TimestampMixin


class DeliverySetting(Base, TimestampMixin):
    __tablename__ = "delivery_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # chatwork/slack/discord/email
    destination: Mapped[str] = mapped_column(String(500), nullable=False)  # room_id, webhook_url, email
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
