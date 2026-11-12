"""SCD2 build orchestration: load snapshots + rules + overrides, run the zipper,
persist immutable chain rows, detect cross-source conflicts, report invariants."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.algorithms.conflict_merge import (
    dedupe_latest,
    detect_conflicts,
    overrides_from_resolutions,
)
from src.algorithms.scd2 import AttributeRule, Override, Snapshot, build_zipper
from src.config.celery_app import celery_app
from src.constants.build_status import BuildStatus, RunMode
from src.constants.conflict_status import ConflictStatus
from src.constants.messages import MSG_BUILD_NOT_FOUND, MSG_RUN_BUSY
from src.models.build_run import BuildRun
from src.models.conflict_item import ConflictItem
from src.models.customer_snapshot import CustomerSnapshot
from src.models.dim_customer import DimCustomer
from src.models.merge_rule import MergeRule
from src.models.source_system import SourceSystem
from src.utils.hashing import stable_hash
from src.utils.logger import log_event


def _rules(db: Session) -> list[AttributeRule]:
    rows = db.execute(select(MergeRule).order_by(MergeRule.id)).scalars().all()
    return [
        AttributeRule(
            key=row.attribute_key,
            source_priority=tuple(row.source_priority or ()),
            normalization=row.normalization,
            exclude_from_change=row.exclude_from_change,
        )
        for row in rows
    ]


def _snapshots(db: Session) -> list[Snapshot]:
    trust_by_source = {
        row.code: row.trust_level for row in db.execute(select(SourceSystem)).scalars().all()
    }
    rows = db.execute(select(CustomerSnapshot).order_by(CustomerSnapshot.id)).scalars().all()
    return [
        Snapshot(
            business_key=row.business_key,
            source_code=row.source_code,
            snapshot_date=row.snapshot_date,
            attributes=row.attributes,
            ingested_at=row.ingested_at,
            trust=trust_by_source.get(row.source_code, 0),
        )
        for row in rows
    ]


def _overrides(db: Session) -> list[Override]:
    rows = db.execute(
        select(ConflictItem).where(ConflictItem.status.in_([ConflictStatus.RESOLVED.value, ConflictStatus.MANUAL.value]))
    ).scalars().all()
    payload = [
        {
            "id": row.id,
            "business_key": row.business_key,
            "attribute_key": row.attribute_key,
            "snapshot_date": row.snapshot_date,
            "resolution": row.resolution or {},
        }
        for row in rows
    ]
    return [
        Override(
            business_key=item["business_key"],
            attribute_key=item["attribute_key"],
            value=item["value"],
            effective_date=item["effective_date"],
            conflict_id=item.get("conflict_id"),
            note=item.get("note", ""),
        )
        for item in overrides_from_resolutions(payload)
    ]


def latest_run(db: Session) -> BuildRun | None:
    return (
        db.execute(
            select(BuildRun)
            .where(BuildRun.status == BuildStatus.SUCCEEDED.value)
            .order_by(BuildRun.id.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def get_run(db: Session, run_id: int) -> BuildRun:
    run = db.get(BuildRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=MSG_BUILD_NOT_FOUND)
    return run


def run_payload(run: BuildRun) -> dict:
    return {
        "id": run.id,
        "run_no": run.run_no,
        "label": run.label,
        "mode": run.mode,
        "status": run.status,
        "triggered_by": run.triggered_by,
        "as_of_cutoff": run.as_of_cutoff.isoformat() if run.as_of_cutoff else None,
        "started_at": run.started_at.isoformat(sep=" ", timespec="seconds") if run.started_at else None,
        "finished_at": run.finished_at.isoformat(sep=" ", timespec="seconds") if run.finished_at else None,
        "stats": run.stats or {},
        "invariants": run.invariants or {},
        "input_hash": run.input_hash,
        "previous_run_id": run.previous_run_id,
        "notes": run.notes,
        "error_message": run.error_message,
    }


def list_runs(db: Session, limit: int = 20) -> list[dict]:
    rows = db.execute(select(BuildRun).order_by(BuildRun.id.desc()).limit(limit)).scalars().all()
    return [run_payload(run) for run in rows]


def next_run_no(db: Session) -> int:
    current = db.execute(select(func.max(BuildRun.run_no))).scalar()
    return int(current or 0) + 1


def create_run(
    db: Session,
    *,
    actor_email: str,
    label: str | None = None,
    notes: str = "",
    dispatch: bool = True,
) -> BuildRun:
    busy = db.execute(
        select(BuildRun).where(BuildRun.status.in_([BuildStatus.PENDING.value, BuildStatus.RUNNING.value]))
    ).scalar_one_or_none()
    if busy is not None:
        raise HTTPException(status_code=409, detail=MSG_RUN_BUSY)
    run_no = next_run_no(db)
    run = BuildRun(
        run_no=run_no,
        label=label or f"run-{run_no}",
        mode=RunMode.FULL.value,
        status=BuildStatus.PENDING.value,
        triggered_by=actor_email or "seed",
        notes=notes,
    )
    previous = latest_run(db)
    run.previous_run_id = previous.id if previous else None
    db.add(run)
    db.commit()
    db.refresh(run)
    if dispatch:
        celery_app.send_task("scdchain.run_build", args=[run.id])
    log_event("BUILD_RUN_CREATED", run_id=run.id, run_no=run.run_no, actor=actor_email)
    return run


def _upsert_conflicts(db: Session, detected, source_names: dict[str, str], run_id: int) -> dict:
    existing = {
        (row.business_key, row.attribute_key): row
        for row in db.execute(select(ConflictItem)).scalars().all()
    }
    auto = 0
    open_items = 0
    for item in detected:
        candidates = item.as_payload()["candidates"]
        row = existing.get((item.business_key, item.attribute_key))
        if row is not None:
            row.candidates = candidates
            row.verdict = item.verdict
            row.similarity = round(float(item.similarity), 4)
            row.snapshot_date = item.snapshot_date
            continue
        if item.verdict == "conflict":
            status = ConflictStatus.OPEN.value
            resolution: dict = {}
            open_items += 1
        else:
            status = ConflictStatus.RESOLVED.value
            resolution = {
                "strategy": item.strategy,
                "value": item.winner_value,
                "display_value": item.winner_value,
                "source": item.winner_source,
                "source_name": source_names.get(item.winner_source, item.winner_source),
                "similarity": round(float(item.similarity), 4),
                "note": "构建期按归一化策略自动收敛",
                "effective_date": (item.snapshot_date + timedelta(days=1)).isoformat(),
            }
            auto += 1
        db.add(
            ConflictItem(
                business_key=item.business_key,
                attribute_key=item.attribute_key,
                snapshot_date=item.snapshot_date,
                candidates=candidates,
                verdict=item.verdict,
                similarity=round(float(item.similarity), 4),
                status=status,
                resolution=resolution,
                resolved_by="system:merge-rule" if status == ConflictStatus.RESOLVED.value else "",
                resolved_at=datetime.now() if status == ConflictStatus.RESOLVED.value else None,
                first_run_id=run_id,
            )
        )
    return {"auto": auto, "open": open_items}


def _chain_keys(db: Session, run_id: int) -> dict[tuple, dict]:
    rows = db.execute(select(DimCustomer).where(DimCustomer.build_run_id == run_id)).scalars().all()
    return {
        (row.business_key, row.valid_from): {
            "business_key": row.business_key,
            "valid_from": row.valid_from.isoformat(),
            "valid_to": row.valid_to.isoformat() if row.valid_to else None,
            "version": row.version,
            "version_source": row.version_source,
            "change_fields": row.change_fields,
            "attributes": row.attributes,
        }
        for row in rows
    }


def _diff_against(previous_id: int | None, current_id: int, db: Session) -> dict:
    if previous_id is None:
        return {"new_chains": 0, "removed_chains": 0, "changed_versions": 0}
    previous = _chain_keys(db, previous_id)
    current = _chain_keys(db, current_id)
    previous_keys = {(key[0], key[1]) for key in previous}
    current_keys = {(key[0], key[1]) for key in current}
    new_chains = len(current_keys - previous_keys)
    removed_chains = len(previous_keys - current_keys)
    changed_keys = len(
        {
            business_key
            for (business_key, valid_from) in current_keys
            if (business_key, valid_from) in previous
            and current[(business_key, valid_from)]["attributes"] != previous[(business_key, valid_from)]["attributes"]
        }
    )
    return {"new_chains": new_chains, "removed_chains": removed_chains, "changed_versions": changed_keys}


def execute_run(db: Session, run_id: int) -> dict:
    run = db.get(BuildRun, run_id)
    if run is None:
        return {"ok": False, "error": "run not found"}
    run.status = BuildStatus.RUNNING.value
    run.started_at = datetime.now()
    db.commit()
    try:
        rules = _rules(db)
        snapshots = _snapshots(db)
        overrides = _overrides(db)
        sources = {row.code: row for row in db.execute(select(SourceSystem)).scalars().all()}
        display_names = {rule.key: (rule.key) for rule in rules}
        rule_rows = db.execute(select(MergeRule)).scalars().all()
        display_names = {row.attribute_key: row.display_name for row in rule_rows}
        source_names = {code: row.name for code, row in sources.items()}

        outcome = build_zipper(snapshots, rules, overrides=overrides)

        db.execute(delete(DimCustomer).where(DimCustomer.build_run_id == run.id))
        for version in outcome.versions:
            db.add(
                DimCustomer(
                    build_run_id=run.id,
                    business_key=version.business_key,
                    version=version.version,
                    attributes=version.attributes,
                    valid_from=version.valid_from,
                    valid_to=version.valid_to,
                    is_current=version.is_current,
                    version_source=version.version_source,
                    change_fields=version.change_fields,
                )
            )
        db.flush()

        detected = dedupe_latest(detect_conflicts(snapshots, rules, display_names, source_names))
        _upsert_conflicts(db, detected, source_names, run.id)
        db.flush()

        snapshot_dates = sorted({row.snapshot_date for row in snapshots})
        as_of_cutoff = snapshot_dates[-1] if snapshot_dates else None
        input_hash = stable_hash(
            {
                "snapshots": [
                    [row.business_key, row.source_code, row.snapshot_date.isoformat(), row.attributes, row.ingested_at.isoformat()]
                    for row in sorted(snapshots, key=lambda item: (item.business_key, item.snapshot_date, item.source_code))
                ],
                "rules": [
                    [rule.key, list(rule.source_priority), rule.normalization, rule.exclude_from_change]
                    for rule in rules
                ],
                "overrides": [
                    [item.business_key, item.attribute_key, item.value, item.effective_date.isoformat()]
                    for item in overrides
                ],
            }
        )

        previous_id = run.previous_run_id
        stats = dict(outcome.stats)
        stats.update(
            {
                "conflicts_detected": len(detected),
                "conflicts_auto_resolved": len(detected) - sum(1 for item in detected if item.verdict == "conflict"),
                "conflicts_open": sum(1 for item in detected if item.verdict == "conflict"),
                "snapshot_dates": [day.isoformat() for day in snapshot_dates],
                "as_of_cutoff": as_of_cutoff.isoformat() if as_of_cutoff else None,
                "previous_run_id": previous_id,
            }
        )
        stats.update(_diff_against(previous_id, run.id, db))

        run.status = BuildStatus.SUCCEEDED.value
        run.finished_at = datetime.now()
        run.as_of_cutoff = as_of_cutoff
        run.stats = stats
        run.invariants = outcome.invariants
        run.input_hash = input_hash
        db.commit()
        log_event(
            "BUILD_RUN_SUCCEEDED",
            run_id=run.id,
            chains=stats.get("chains_total"),
            new_chains=stats.get("new_chains"),
            invariants_passed=outcome.invariants.get("all_passed"),
        )
        return {"ok": True, "run_id": run.id, "stats": stats, "invariants": outcome.invariants}
    except Exception as exc:  # keep the batch in a failed state with the real error
        db.rollback()
        run = db.get(BuildRun, run_id)
        if run is not None:
            run.status = BuildStatus.FAILED.value
            run.finished_at = datetime.now()
            run.error_message = f"{type(exc).__name__}: {exc}"[:500]
            db.commit()
        log_event("BUILD_RUN_FAILED", run_id=run_id, error=f"{type(exc).__name__}: {exc}")
        return {"ok": False, "run_id": run_id, "error": str(exc)}


def run_detail(db: Session, run_id: int) -> dict:
    run = get_run(db, run_id)
    payload = run_payload(run)
    if run.previous_run_id:
        previous = db.get(BuildRun, run.previous_run_id)
        payload["previous"] = run_payload(previous) if previous else None
    current = _chain_keys(db, run.id)
    payload["chain_samples"] = list(current.values())[:12]
    return payload


def compare_runs(db: Session, left_id: int, right_id: int) -> dict:
    left = get_run(db, left_id)
    right = get_run(db, right_id)
    left_chains = _chain_keys(db, left.id)
    right_chains = _chain_keys(db, right.id)
    new_chain_keys = sorted(set(right_chains) - set(left_chains))
    removed_chain_keys = sorted(set(left_chains) - set(right_chains))
    changed_current = []
    for (business_key, valid_from) in sorted(set(left_chains) & set(right_chains)):
        left_row = left_chains[(business_key, valid_from)]
        right_row = right_chains[(business_key, valid_from)]
        if left_row["attributes"] != right_row["attributes"]:
            changed_current.append(
                {
                    "business_key": business_key,
                    "valid_from": left_row["valid_from"],
                    "left": left_row["attributes"],
                    "right": right_row["attributes"],
                }
            )
    current_changes = []
    for business_key in {key[0] for key in right_chains}:
        left_current = [row for (key, _), row in left_chains.items() if key == business_key and row.get("valid_to") is None]
        right_current = [row for (key, _), row in right_chains.items() if key == business_key and row.get("valid_to") is None]
        if left_current and right_current and left_current[0]["attributes"] != right_current[0]["attributes"]:
            current_changes.append(
                {
                    "business_key": business_key,
                    "left": left_current[0]["attributes"],
                    "right": right_current[0]["attributes"],
                    "right_valid_from": right_current[0]["valid_from"],
                    "version_source": right_current[0]["version_source"],
                }
            )
    return {
        "left": run_payload(left),
        "right": run_payload(right),
        "new_chains": len(new_chain_keys),
        "removed_chains": len(removed_chain_keys),
        "changed_versions": len(changed_current),
        "changed_keys": len({item["business_key"] for item in current_changes}),
        "new_chain_samples": [right_chains[key] for key in new_chain_keys[:20]],
        "removed_chain_samples": [left_chains[key] for key in removed_chain_keys[:20]],
        "current_change_samples": current_changes[:20],
    }
