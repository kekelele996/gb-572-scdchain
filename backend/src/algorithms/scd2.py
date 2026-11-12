"""SCD2 zipper builder — pure, deterministic, no database access.

Input : raw daily snapshots of the customer dimension from three source systems.
Output: version chains with ``valid_from / valid_to / is_current / version``,
        build statistics and the four invariant checks.

Rules implemented
-----------------
1. Group by business key, then walk snapshot dates in ascending order.
2. Compare the *golden* attribute set of each day against the open chain; a
   non-empty changed-field set (excluding ignored columns) closes the old chain
   at the observation date (``valid_to = D``) and opens a new one effective
   ``D + 1`` (nightly batch, next-day effective — this is why an as-of query on
   D still sees the previous level).
3. Several source rows for the same key/day are folded into one golden value
   before comparing (same-day changes collapse, ``collapsed_same_day`` counts them).
4. Out-of-order (late) snapshots: rows are replayed in *ingestion* order; a row
   dated before the running maximum is counted as a late arrival and the key's
   chain is re-derived from the retained history (backfill).
5. Manual overrides resolved on the conflict queue are appended as
   ``version_source = "manual"`` versions effective on the configured date.
6. Invariants: one current row per key, non-overlapping intervals, no gaps,
   ``valid_from <= valid_to``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Iterable

from .normalization import canonical_value

DAY = timedelta(days=1)


@dataclass(frozen=True)
class AttributeRule:
    key: str
    source_priority: tuple[str, ...] = ()
    normalization: str = "direct"
    exclude_from_change: bool = False


@dataclass
class Snapshot:
    business_key: str
    source_code: str
    snapshot_date: date
    attributes: dict[str, Any]
    ingested_at: datetime
    trust: int = 0


@dataclass
class Override:
    business_key: str
    attribute_key: str
    value: str
    effective_date: date
    conflict_id: int | None = None
    note: str = ""


@dataclass
class Version:
    business_key: str
    version: int
    valid_from: date
    valid_to: date | None
    attributes: dict[str, Any]
    change_fields: list[str] = field(default_factory=list)
    version_source: str = "merge"
    is_current: bool = False


@dataclass
class BuildOutcome:
    versions: list[Version]
    stats: dict[str, Any]
    invariants: dict[str, Any]


def _golden_attributes(group: list[Snapshot], rules: Iterable[AttributeRule]) -> dict[str, str]:
    """One golden value per attribute, choosing the highest-priority present source."""
    by_source = {row.source_code: row for row in group}
    golden: dict[str, str] = {}
    for rule in rules:
        value = ""
        for source_code in rule.source_priority:
            row = by_source.get(source_code)
            if row is None:
                continue
            raw = row.attributes.get(rule.key)
            if raw is None or str(raw).strip() == "":
                continue
            value = canonical_value(rule.normalization, raw)
            break
        golden[rule.key] = value
    return golden


def _changed_fields(
    previous: dict[str, Any],
    current: dict[str, Any],
    rules: Iterable[AttributeRule],
) -> list[str]:
    changed: list[str] = []
    for rule in rules:
        if rule.exclude_from_change:
            continue
        before = canonical_value(rule.normalization, previous.get(rule.key))
        after = canonical_value(rule.normalization, current.get(rule.key))
        if before != after:
            changed.append(rule.key)
    return changed


def derive_versions(
    business_key: str,
    rows: list[Snapshot],
    rules: Iterable[AttributeRule],
) -> tuple[list[Version], int]:
    """Canonical chain derivation for one key (date ordered)."""
    by_date: dict[date, list[Snapshot]] = {}
    for row in rows:
        by_date.setdefault(row.snapshot_date, []).append(row)

    collapsed = 0
    for group in by_date.values():
        collapsed += max(0, len({row.source_code for row in group}) - 1)

    golden_by_date = {day: _golden_attributes(group, rules) for day, group in by_date.items()}

    versions: list[Version] = []
    for day in sorted(golden_by_date):
        attributes = golden_by_date[day]
        if not versions:
            versions.append(
                Version(business_key=business_key, version=0, valid_from=day, valid_to=None, attributes=attributes)
            )
            continue
        current = versions[-1]
        changed = _changed_fields(current.attributes, attributes, rules)
        if not changed:
            continue
        current.valid_to = day
        start = day + DAY
        if start <= current.valid_from:  # defensive: never produce an inverted interval
            start = current.valid_from + DAY
        versions.append(
            Version(
                business_key=business_key,
                version=0,
                valid_from=start,
                valid_to=None,
                attributes=attributes,
                change_fields=changed,
            )
        )
    return versions, collapsed


def apply_overrides(
    business_key: str,
    versions: list[Version],
    overrides: list[Override],
    rules: dict[str, AttributeRule],
) -> int:
    """Append manual-override versions; returns how many were appended."""
    applied = 0
    if not versions:
        return applied
    for override in sorted(overrides, key=lambda item: (item.effective_date, item.attribute_key)):
        rule = rules.get(override.attribute_key)
        if rule is None:
            continue
        value = canonical_value(rule.normalization, override.value)
        last = versions[-1]
        if canonical_value(rule.normalization, last.attributes.get(override.attribute_key)) == value:
            continue
        if override.effective_date <= last.valid_from:
            # Override older than the open version: update in place (no new chain).
            last.attributes = {**last.attributes, override.attribute_key: value}
            if override.attribute_key not in last.change_fields:
                last.change_fields = [*last.change_fields, override.attribute_key]
            continue
        last.valid_to = override.effective_date - DAY
        versions.append(
            Version(
                business_key=business_key,
                version=0,
                valid_from=override.effective_date,
                valid_to=None,
                attributes={**last.attributes, override.attribute_key: value},
                change_fields=[override.attribute_key],
                version_source="manual",
            )
        )
        applied += 1
    return applied


def finalize(versions_by_key: dict[str, list[Version]]) -> list[Version]:
    """Sort, number and mark the current row for every key."""
    output: list[Version] = []
    for business_key in sorted(versions_by_key):
        versions = sorted(versions_by_key[business_key], key=lambda item: item.valid_from)
        for index, version in enumerate(versions, start=1):
            version.business_key = business_key
            version.version = index
            version.is_current = index == len(versions)
            if version.is_current:
                version.valid_to = None
        output.extend(versions)
    return output


def validate(versions_by_key: dict[str, list[Version]]) -> dict[str, Any]:
    uniqueness_failed: list[str] = []
    overlap_failed: list[str] = []
    gap_failed: list[str] = []
    order_failed: list[str] = []

    for business_key, versions in versions_by_key.items():
        ordered = sorted(versions, key=lambda item: item.valid_from)
        current_rows = [version for version in ordered if version.is_current]
        if len(current_rows) != 1:
            uniqueness_failed.append(business_key)
        previous: Version | None = None
        for version in ordered:
            if version.valid_to is not None and version.valid_from > version.valid_to:
                order_failed.append(business_key)
            if previous is not None:
                if previous.valid_to is None:
                    overlap_failed.append(business_key)
                elif version.valid_from <= previous.valid_to:
                    overlap_failed.append(business_key)
                elif version.valid_from != previous.valid_to + DAY:
                    gap_failed.append(business_key)
            previous = version

    total = len(versions_by_key)

    def block(passed: int, failed: list[str]) -> dict[str, Any]:
        return {"passed": passed, "total": total, "failed_keys": sorted(set(failed))[:20]}

    report = {
        "uniqueness": block(total - len(set(uniqueness_failed)), uniqueness_failed),
        "overlap": block(total - len(set(overlap_failed)), overlap_failed),
        "gap": block(total - len(set(gap_failed)), gap_failed),
        "order": block(total - len(set(order_failed)), order_failed),
    }
    report["all_passed"] = all(
        report[key]["passed"] == total for key in ("uniqueness", "overlap", "gap", "order")
    )
    return report


def build_zipper(
    snapshots: list[Snapshot],
    rules: list[AttributeRule],
    overrides: list[Override] | None = None,
    as_of_cutoff: date | None = None,
) -> BuildOutcome:
    overrides = overrides or []
    rule_map = {rule.key: rule for rule in rules}

    rows = [row for row in snapshots if as_of_cutoff is None or row.snapshot_date <= as_of_cutoff]

    by_key: dict[str, list[Snapshot]] = {}
    for row in rows:
        by_key.setdefault(row.business_key, []).append(row)

    versions_by_key: dict[str, list[Version]] = {}
    late_arrivals = 0
    collapsed_same_day = 0

    for business_key, key_rows in by_key.items():
        # Replay in ingestion order: anything older than the running maximum is late.
        ordered = sorted(key_rows, key=lambda row: (row.ingested_at, row.snapshot_date, row.source_code))
        max_seen: date | None = None
        for row in ordered:
            if max_seen is not None and row.snapshot_date < max_seen:
                late_arrivals += 1
            max_seen = row.snapshot_date if max_seen is None else max(max_seen, row.snapshot_date)

        versions, collapsed = derive_versions(business_key, key_rows, rules)
        collapsed_same_day += collapsed
        versions_by_key[business_key] = versions

    applied_overrides = 0
    override_groups: dict[str, list[Override]] = {}
    for override in overrides:
        override_groups.setdefault(override.business_key, []).append(override)
    for business_key, key_overrides in override_groups.items():
        if business_key not in versions_by_key:
            continue
        applied_overrides += apply_overrides(business_key, versions_by_key[business_key], key_overrides, rule_map)

    versions = finalize(versions_by_key)
    invariants = validate(versions_by_key)

    closed = sum(1 for version in versions if not version.is_current)
    changed_keys = sum(1 for key_versions in versions_by_key.values() if len(key_versions) > 1)
    stats = {
        "snapshots_used": len(rows),
        "customers": len(versions_by_key),
        "chains_total": len(versions),
        "chains_closed": closed,
        "changed_keys": changed_keys,
        "changes": sum(max(0, len(key_versions) - 1) for key_versions in versions_by_key.values()),
        "late_arrivals": late_arrivals,
        "collapsed_same_day": collapsed_same_day,
        "overrides_applied": applied_overrides,
        "ignored_columns": sorted(rule.key for rule in rules if rule.exclude_from_change),
    }
    return BuildOutcome(versions=versions, stats=stats, invariants=invariants)
