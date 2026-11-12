from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class ConflictItem(Base):
    """Cross-source attribute disagreement with its normalisation verdict and resolution trace."""

    __tablename__ = "conflict_items"
    __table_args__ = (UniqueConstraint("business_key", "attribute_key", name="uq_conflict_key_attr"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    business_key: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    attribute_key: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    candidates: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    verdict: Mapped[str] = mapped_column(String(24), nullable=False, default="conflict")
    similarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False, index=True)
    resolution: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    resolved_by: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
