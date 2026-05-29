from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from .mixins import TimestampMixin


class Store(Base, TimestampMixin):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    data_sources: Mapped[list["DataSource"]] = relationship(back_populates="store", cascade="all, delete-orphan")
    machine_results: Mapped[list["MachineResult"]] = relationship(back_populates="store")
    unit_results: Mapped[list["UnitResult"]] = relationship(back_populates="store")
