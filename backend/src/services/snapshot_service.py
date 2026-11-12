"""Ingested snapshot feed inspection (upstream input for the zipper)."""
from __future__ import annotations

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from src.models.customer_snapshot import CustomerSnapshot
from src.models.source_system import SourceSystem


def feed_summary(db: Session) -> dict:
    rows = db.execute(
        select(
            CustomerSnapshot.snapshot_date,
            CustomerSnapshot.source_code,
            func.count(CustomerSnapshot.id),
            func.coalesce(func.sum(cast(CustomerSnapshot.is_late, Integer)), 0),
        )
        .group_by(CustomerSnapshot.snapshot_date, CustomerSnapshot.source_code)
        .order_by(CustomerSnapshot.snapshot_date, CustomerSnapshot.source_code)
    ).all()
    batches: list[dict] = []
    total = 0
    for snapshot_date, source_code, count, late in rows:
        total += int(count)
        batches.append(
            {
                "snapshot_date": snapshot_date.isoformat(),
                "source_code": source_code,
                "rows": int(count),
                "late_rows": int(late or 0),
            }
        )
    dates = sorted({batch["snapshot_date"] for batch in batches})
    return {"total_rows": total, "snapshot_dates": dates, "batches": batches}


def recent_rows(db: Session, limit: int = 20) -> list[dict]:
    sources = {source.id: source for source in db.execute(select(SourceSystem)).scalars().all()}
    rows = db.execute(select(CustomerSnapshot).order_by(CustomerSnapshot.id.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "source_code": row.source_code,
            "source_name": sources[row.source_id].name if row.source_id in sources else row.source_code,
            "business_key": row.business_key,
            "snapshot_date": row.snapshot_date.isoformat(),
            "attributes": row.attributes,
            "ingested_at": row.ingested_at.isoformat(sep=" ", timespec="minutes"),
            "is_late": row.is_late,
            "batch_tag": row.batch_tag,
        }
        for row in rows
    ]
