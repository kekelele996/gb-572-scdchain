"""Current dimension browsing, as-of time travel, per-key chain history and overview."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.constants.build_status import BuildStatus
from src.constants.conflict_status import ConflictStatus, STRATEGY_LABELS
from src.models.build_run import BuildRun
from src.models.conflict_item import ConflictItem
from src.models.customer_snapshot import CustomerSnapshot
from src.models.dim_customer import DimCustomer
from src.services import build_service
from src.utils.pagination import Pagination, as_page

DIM_COLUMNS = ("business_key", "full_name", "mobile", "org_code", "customer_level", "city", "channel")


def _latest_run(db: Session) -> BuildRun | None:
    return build_service.latest_run(db)


def _row_payload(row: DimCustomer) -> dict:
    attributes = row.attributes or {}
    return {
        "business_key": row.business_key,
        "version": row.version,
        "full_name": attributes.get("full_name", ""),
        "mobile": attributes.get("mobile", ""),
        "org_code": attributes.get("org_code", ""),
        "customer_level": attributes.get("customer_level", ""),
        "city": attributes.get("city", ""),
        "channel": attributes.get("channel", ""),
        "valid_from": row.valid_from.isoformat(),
        "valid_to": row.valid_to.isoformat() if row.valid_to else None,
        "is_current": row.is_current,
        "version_source": row.version_source,
        "change_fields": row.change_fields or [],
        "attributes": attributes,
    }


def _filters(query, search: str, level: str):
    if search:
        like = f"%{search.strip()}%"
        query = query.where(
            or_(
                DimCustomer.business_key.ilike(like),
                DimCustomer.attributes["full_name"].astext.ilike(like),
                DimCustomer.attributes["org_code"].astext.ilike(like),
            )
        )
    if level:
        query = query.where(DimCustomer.attributes["customer_level"].astext == level)
    return query


def current_dims(db: Session, search: str, level: str, pagination: Pagination) -> dict:
    run = _latest_run(db)
    if run is None:
        return {"items": [], "total": 0, "page": pagination.page, "page_size": pagination.page_size, "pages": 1,
                "run": None, "level_distribution": {}}
    base = select(DimCustomer).where(DimCustomer.build_run_id == run.id, DimCustomer.is_current.is_(True))
    base = _filters(base, search, level)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = (
        db.execute(base.order_by(DimCustomer.business_key).offset(pagination.offset).limit(pagination.page_size))
        .scalars()
        .all()
    )
    distribution_rows = db.execute(
        select(DimCustomer.attributes["customer_level"].astext, func.count(DimCustomer.id))
        .where(DimCustomer.build_run_id == run.id, DimCustomer.is_current.is_(True))
        .group_by(DimCustomer.attributes["customer_level"].astext)
    ).all()
    distribution = {level_name or "未知": int(count) for level_name, count in distribution_rows}
    payload = as_page([_row_payload(row) for row in rows], int(total), pagination)
    payload.update({"run": build_service.run_payload(run), "level_distribution": distribution})
    return payload


def as_of_query(db: Session, as_of: date, search: str, level: str, pagination: Pagination) -> dict:
    run = _latest_run(db)
    if run is None:
        return {"items": [], "total": 0, "page": pagination.page, "page_size": pagination.page_size, "pages": 1,
                "run": None, "as_of": as_of.isoformat(), "effective_on_day": 0}
    base = select(DimCustomer).where(
        DimCustomer.build_run_id == run.id,
        DimCustomer.valid_from <= as_of,
        or_(DimCustomer.valid_to.is_(None), DimCustomer.valid_to >= as_of),
    )
    base = _filters(base, search, level)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = (
        db.execute(base.order_by(DimCustomer.business_key).offset(pagination.offset).limit(pagination.page_size))
        .scalars()
        .all()
    )
    effective = db.execute(
        select(func.count(DimCustomer.id)).where(
            DimCustomer.build_run_id == run.id,
            DimCustomer.valid_from == as_of + timedelta(days=1),
        )
    ).scalar() or 0
    payload = as_page([_row_payload(row) for row in rows], int(total), pagination)
    payload.update(
        {
            "run": build_service.run_payload(run),
            "as_of": as_of.isoformat(),
            "effective_on_day": int(effective),
            "changes_effective_next_day": int(effective),
        }
    )
    return payload


def as_of_rows(db: Session, as_of: date) -> list[DimCustomer]:
    run = _latest_run(db)
    if run is None:
        return []
    return (
        db.execute(
            select(DimCustomer)
            .where(
                DimCustomer.build_run_id == run.id,
                DimCustomer.valid_from <= as_of,
                or_(DimCustomer.valid_to.is_(None), DimCustomer.valid_to >= as_of),
            )
            .order_by(DimCustomer.business_key)
        )
        .scalars()
        .all()
    )


def history(db: Session, business_key: str) -> dict:
    run = _latest_run(db)
    if run is None:
        raise HTTPException(status_code=404, detail="尚无成功构建，维度为空")
    versions = (
        db.execute(
            select(DimCustomer)
            .where(DimCustomer.build_run_id == run.id, DimCustomer.business_key == business_key)
            .order_by(DimCustomer.version)
        )
        .scalars()
        .all()
    )
    conflicts = (
        db.execute(select(ConflictItem).where(ConflictItem.business_key == business_key).order_by(ConflictItem.id))
        .scalars()
        .all()
    )
    snapshots = (
        db.execute(
            select(CustomerSnapshot)
            .where(CustomerSnapshot.business_key == business_key)
            .order_by(CustomerSnapshot.snapshot_date, CustomerSnapshot.source_code)
        )
        .scalars()
        .all()
    )
    if not versions and not snapshots:
        raise HTTPException(status_code=404, detail="客户业务键不存在")
    return {
        "business_key": business_key,
        "run": build_service.run_payload(run),
        "versions": [_row_payload(row) for row in versions],
        "conflicts": [
            {
                "id": row.id,
                "attribute_key": row.attribute_key,
                "snapshot_date": row.snapshot_date.isoformat(),
                "status": row.status,
                "verdict": row.verdict,
                "similarity": row.similarity,
                "candidates": row.candidates,
                "resolution": row.resolution,
            }
            for row in conflicts
        ],
        "snapshots": [
            {
                "source_code": row.source_code,
                "snapshot_date": row.snapshot_date.isoformat(),
                "attributes": row.attributes,
                "ingested_at": row.ingested_at.isoformat(sep=" ", timespec="minutes"),
                "is_late": row.is_late,
            }
            for row in snapshots
        ],
    }


def overview(db: Session) -> dict:
    run = _latest_run(db)
    snapshot_rows = db.execute(select(func.count()).select_from(CustomerSnapshot)).scalar() or 0
    snapshot_dates = [
        row[0].isoformat()
        for row in db.execute(select(CustomerSnapshot.snapshot_date).distinct().order_by(CustomerSnapshot.snapshot_date))
    ]
    conflict_rows = db.execute(
        select(ConflictItem.status, func.count(ConflictItem.id)).group_by(ConflictItem.status)
    ).all()
    conflicts = {status: int(count) for status, count in conflict_rows}
    strategy_rows = db.execute(
        select(ConflictItem.resolution["strategy"].astext, func.count(ConflictItem.id)).group_by(
            ConflictItem.resolution["strategy"].astext
        )
    ).all()
    strategies = {
        (strategy or "open"): int(count) for strategy, count in strategy_rows if count
    }
    level_rows = db.execute(
        select(DimCustomer.attributes["customer_level"].astext, func.count(DimCustomer.id))
        .where(DimCustomer.build_run_id == (run.id if run else -1), DimCustomer.is_current.is_(True))
        .group_by(DimCustomer.attributes["customer_level"].astext)
    ).all()
    dim_rows = db.execute(
        select(func.count(DimCustomer.id)).where(
            DimCustomer.build_run_id == (run.id if run else -1), DimCustomer.is_current.is_(True)
        )
    ).scalar() or 0
    return {
        "brand": "scdchain",
        "snapshot_rows": int(snapshot_rows),
        "snapshot_dates": snapshot_dates,
        "latest_run": build_service.run_payload(run) if run else None,
        "current_customers": int(dim_rows),
        "level_distribution": {level_name or "未知": int(count) for level_name, count in level_rows},
        "conflicts": {"by_status": conflicts, "by_strategy": strategies,
                      "open": conflicts.get(ConflictStatus.OPEN.value, 0),
                      "total": sum(conflicts.values())},
        "asof_demo": {"business_key": "CUST-0060", "as_of": "2026-11-05"},
        "strategy_labels": STRATEGY_LABELS,
    }
