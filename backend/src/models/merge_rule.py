from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base


class MergeRule(Base):
    """Per-attribute merge policy: which source wins, how values are normalised."""

    __tablename__ = "merge_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    attribute_key: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(48), nullable=False)
    data_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_priority: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    normalization: Mapped[str] = mapped_column(String(24), nullable=False, default="direct")
    exclude_from_change: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    updated_by: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
