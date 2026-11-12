from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class BuildRun(Base):
    """One SCD2 build batch (triggered by API or by the demo seed)."""

    __tablename__ = "build_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    mode: Mapped[str] = mapped_column(String(16), default="full", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    triggered_by: Mapped[str] = mapped_column(String(120), default="seed", nullable=False)
    as_of_cutoff: Mapped[date | None] = mapped_column(Date, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    stats: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    invariants: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    input_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    previous_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    notes: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
