"""Dimension design: merge rules and source system catalogue."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants.customer_attribute import ATTRIBUTES
from src.constants.messages import MSG_RULE_NOT_FOUND, MSG_RULE_PRIORITY_INVALID
from src.constants.normalization import NormalizationStrategy
from src.models.merge_rule import MergeRule
from src.models.source_system import SourceSystem

ATTRIBUTE_BY_KEY = {attribute["key"]: attribute for attribute in ATTRIBUTES}


def list_sources(db: Session) -> list[dict]:
    rows = db.execute(select(SourceSystem).order_by(SourceSystem.trust_level.desc())).scalars().all()
    return [
        {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "system_type": row.system_type,
            "description": row.description,
            "contact_owner": row.contact_owner,
            "snapshot_time": row.snapshot_time,
            "trust_level": row.trust_level,
            "is_active": row.is_active,
        }
        for row in rows
    ]


def list_rules(db: Session) -> list[dict]:
    rules = db.execute(select(MergeRule).order_by(MergeRule.id)).scalars().all()
    sources = {source["code"]: source for source in list_sources(db)}
    result = []
    for rule in rules:
        meta = ATTRIBUTE_BY_KEY.get(rule.attribute_key, {})
        result.append(
            {
                "id": rule.id,
                "attribute_key": rule.attribute_key,
                "display_name": rule.display_name or meta.get("label", rule.attribute_key),
                "data_type": rule.data_type,
                "source_priority": rule.source_priority,
                "normalization": rule.normalization,
                "exclude_from_change": rule.exclude_from_change,
                "description": rule.description,
                "updated_by": rule.updated_by,
                "updated_at": rule.updated_at.isoformat(sep=" ", timespec="seconds") if rule.updated_at else None,
                "enum_values": meta.get("enum_values", []),
                "priority_sources": [
                    {"code": code, "name": sources.get(code, {}).get("name", code)}
                    for code in rule.source_priority
                ],
            }
        )
    return result


def update_rule(db: Session, rule_id: int, payload: dict, actor_email: str) -> dict:
    rule = db.get(MergeRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=MSG_RULE_NOT_FOUND)

    active_codes = [source["code"] for source in list_sources(db) if source["is_active"]]
    priority = payload.get("source_priority")
    if priority is not None:
        if sorted(priority) != sorted(active_codes) or len(set(priority)) != len(priority):
            raise HTTPException(status_code=422, detail=MSG_RULE_PRIORITY_INVALID)
        rule.source_priority = list(priority)

    normalization = payload.get("normalization")
    if normalization is not None:
        if normalization not in {strategy.value for strategy in NormalizationStrategy}:
            raise HTTPException(status_code=422, detail="归一化策略不合法")
        rule.normalization = normalization

    exclude = payload.get("exclude_from_change")
    if exclude is not None:
        rule.exclude_from_change = bool(exclude)

    if payload.get("description") is not None:
        rule.description = str(payload["description"])[:255]

    rule.updated_by = actor_email
    db.commit()
    db.refresh(rule)
    return next(item for item in list_rules(db) if item["id"] == rule.id)
