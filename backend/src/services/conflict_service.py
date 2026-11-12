"""Conflict queue: read models, normalisation verdict display, human adjudication."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.algorithms.normalization import canonical_value
from src.constants.conflict_status import CONFLICT_STATUS_LABELS, STRATEGY_LABELS, ConflictStatus, ResolutionStrategy
from src.constants.customer_attribute import ATTRIBUTES
from src.constants.messages import MSG_CONFLICT_CLOSED, MSG_CONFLICT_NOT_FOUND, MSG_CONFLICT_VALUE_INVALID
from src.models.conflict_item import ConflictItem
from src.models.merge_rule import MergeRule
from src.utils.pagination import Pagination, as_page

ATTRIBUTE_BY_KEY = {attribute["key"]: attribute for attribute in ATTRIBUTES}
VERDICT_LABELS = {
    "normalized_equal": "归一后一致",
    "similar": "同音/近似",
    "conflict": "真实冲突",
}


def _payload(row: ConflictItem, display_name: str = "", normalization: str = "direct") -> dict:
    resolution = row.resolution or {}
    return {
        "id": row.id,
        "business_key": row.business_key,
        "attribute_key": row.attribute_key,
        "display_name": display_name or ATTRIBUTE_BY_KEY.get(row.attribute_key, {}).get("label", row.attribute_key),
        "normalization": normalization,
        "snapshot_date": row.snapshot_date.isoformat(),
        "candidates": row.candidates or [],
        "verdict": row.verdict,
        "verdict_label": VERDICT_LABELS.get(row.verdict, row.verdict),
        "similarity": row.similarity,
        "status": row.status,
        "status_label": CONFLICT_STATUS_LABELS.get(row.status, row.status),
        "resolution": resolution,
        "strategy_label": STRATEGY_LABELS.get(resolution.get("strategy", ""), resolution.get("strategy", "")),
        "resolved_by": row.resolved_by,
        "resolved_at": row.resolved_at.isoformat(sep=" ", timespec="seconds") if row.resolved_at else None,
        "effective_date": resolution.get("effective_date"),
    }


def list_conflicts(db: Session, status: str, pagination: Pagination) -> dict:
    rules = {row.attribute_key: row for row in db.execute(select(MergeRule)).scalars().all()}
    query = select(ConflictItem)
    if status and status != "all":
        query = query.where(ConflictItem.status == status)
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0
    rows = (
        db.execute(query.order_by(ConflictItem.id).offset(pagination.offset).limit(pagination.page_size))
        .scalars()
        .all()
    )
    items = []
    for row in rows:
        rule = rules.get(row.attribute_key)
        items.append(_payload(row, rule.display_name if rule else "", rule.normalization if rule else "direct"))
    return as_page(items, int(total), pagination)


def summary(db: Session) -> dict:
    status_rows = db.execute(select(ConflictItem.status, func.count(ConflictItem.id)).group_by(ConflictItem.status)).all()
    by_status = {status: int(count) for status, count in status_rows}
    verdict_rows = db.execute(select(ConflictItem.verdict, func.count(ConflictItem.id)).group_by(ConflictItem.verdict)).all()
    by_verdict = {verdict: int(count) for verdict, count in verdict_rows}
    strategy_rows = db.execute(
        select(ConflictItem.resolution["strategy"].astext, func.count(ConflictItem.id)).group_by(
            ConflictItem.resolution["strategy"].astext
        )
    ).all()
    by_strategy = {strategy or "open": int(count) for strategy, count in strategy_rows if count}
    return {
        "total": sum(by_status.values()),
        "open": by_status.get(ConflictStatus.OPEN.value, 0),
        "by_status": by_status,
        "by_verdict": by_verdict,
        "by_strategy": by_strategy,
        "labels": {"status": CONFLICT_STATUS_LABELS, "strategy": STRATEGY_LABELS, "verdict": VERDICT_LABELS},
    }


def get_conflict(db: Session, conflict_id: int) -> ConflictItem:
    row = db.get(ConflictItem, conflict_id)
    if row is None:
        raise HTTPException(status_code=404, detail=MSG_CONFLICT_NOT_FOUND)
    return row


def resolve(
    db: Session,
    conflict_id: int,
    *,
    strategy: str,
    value: str,
    note: str,
    actor_email: str,
) -> dict:
    row = get_conflict(db, conflict_id)
    if row.status != ConflictStatus.OPEN.value:
        raise HTTPException(status_code=409, detail=MSG_CONFLICT_CLOSED)
    rule = db.execute(select(MergeRule).where(MergeRule.attribute_key == row.attribute_key)).scalar_one_or_none()
    normalization = rule.normalization if rule else "direct"

    source = ""
    canonical = ""
    if strategy == ResolutionStrategy.CANDIDATE.value:
        candidates = row.candidates or []
        matched = None
        for candidate in candidates:
            if value in (candidate.get("value"), candidate.get("canonical")):
                matched = candidate
                break
        if matched is None:
            raise HTTPException(status_code=422, detail=MSG_CONFLICT_VALUE_INVALID)
        source = matched.get("source_code", "")
        canonical = matched.get("canonical") or canonical_value(normalization, matched.get("value"))
    elif strategy == ResolutionStrategy.MANUAL.value:
        text = (value or "").strip()
        if not text or len(text) > 64:
            raise HTTPException(status_code=422, detail=MSG_CONFLICT_VALUE_INVALID)
        canonical = canonical_value(normalization, text)
        source = "manual"
    else:
        raise HTTPException(status_code=422, detail=MSG_CONFLICT_VALUE_INVALID)

    effective = row.snapshot_date + timedelta(days=1)
    row.status = ConflictStatus.MANUAL.value if strategy == ResolutionStrategy.MANUAL.value else ConflictStatus.RESOLVED.value
    row.resolution = {
        "strategy": strategy,
        "value": canonical,
        "display_value": (value or "").strip(),
        "source": source,
        "note": (note or "")[:200],
        "similarity": 1.0,
        "effective_date": effective.isoformat(),
        "decided_by": actor_email,
        "decided_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
    }
    row.resolved_by = actor_email
    row.resolved_at = datetime.now()
    db.commit()
    db.refresh(row)
    return _payload(row, rule.display_name if rule else "", normalization)
