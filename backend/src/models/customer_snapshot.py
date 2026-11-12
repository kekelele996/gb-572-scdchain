from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class CustomerSnapshot(Base):
    """Raw daily full snapshot from one source system (natural key: source+key+date)."""

    __tablename__ = "customer_snapshots"
    __table_args__ = (
        UniqueConstraint("source_id", "business_key", "snapshot_date", name="uq_snapshot_natural"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source_systems.id"), nullable=False, index=True)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    business_key: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    batch_tag: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
