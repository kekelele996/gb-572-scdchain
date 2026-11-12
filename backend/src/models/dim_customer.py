from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class DimCustomer(Base):
    """SCD2 zipper row. Rows are immutable per build run; the latest run is the visible dimension."""

    __tablename__ = "dim_customers"
    __table_args__ = (
        UniqueConstraint("build_run_id", "business_key", "version", name="uq_dim_run_key_version"),
        Index(
            "uq_dim_run_current",
            "build_run_id",
            "business_key",
            unique=True,
            postgresql_where=text("is_current"),
        ),
        Index("ix_dim_run_asof", "build_run_id", "business_key", "valid_from"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    build_run_id: Mapped[int] = mapped_column(ForeignKey("build_runs.id"), nullable=False, index=True)
    business_key: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version_source: Mapped[str] = mapped_column(String(24), default="merge", nullable=False)
    change_fields: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
