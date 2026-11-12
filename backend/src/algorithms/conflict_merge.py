"""Cross-source conflict detection and merge adjudication — pure, no database access.

Flow
----
1. Group raw snapshots by ``(business_key, snapshot_date)``; a group with two or
   more source systems is a *cross-source candidate window*.
2. For each merge rule, collect the raw value from every source in the window.
   Identical raw values are not a candidate at all.
3. Normalise each raw value (phone digits / org code map / pinyin homophone).
   * all canonical values equal -> ``normalized_equal`` (auto converged);
   * else best pairwise similarity >= 0.85 -> ``similar`` (auto converged to the
     highest-priority source, trace kept);
   * else -> ``conflict`` (goes to the human adjudication queue).
4. A resolution (human candidate pick or manual override) is later turned into
   an SCD2 override effective the next day, so a rebuild reproduces the golden
   record deterministically.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from itertools import combinations
from typing import Any

from .normalization import canonical_value, similarity
from .scd2 import AttributeRule, Snapshot

SIMILARITY_THRESHOLD = 0.85


@dataclass
class Candidate:
    source_code: str
    value: str
    canonical: str
    observed_at: datetime
    trust: int = 0
    source_name: str = ""


@dataclass
class DetectedConflict:
    business_key: str
    snapshot_date: date
    attribute_key: str
    display_name: str
    candidates: list[Candidate] = field(default_factory=list)
    verdict: str = "conflict"  # normalized_equal | similar | conflict
    similarity: float = 0.0
    winner_source: str = ""
    winner_value: str = ""
    strategy: str | None = None

    def as_payload(self) -> dict[str, Any]:
        return {
            "business_key": self.business_key,
            "snapshot_date": self.snapshot_date.isoformat(),
            "attribute_key": self.attribute_key,
            "display_name": self.display_name,
            "verdict": self.verdict,
            "similarity": round(self.similarity, 4),
            "winner_source": self.winner_source,
            "winner_value": self.winner_value,
            "strategy": self.strategy,
            "candidates": [
                {
                    "source_code": candidate.source_code,
                    "source_name": candidate.source_name,
                    "value": candidate.value,
                    "canonical": candidate.canonical,
                    "observed_at": candidate.observed_at.isoformat(sep=" ", timespec="minutes"),
                    "trust": candidate.trust,
                }
                for candidate in self.candidates
            ],
        }


def _priority_order(rule: AttributeRule, sources: set[str]) -> list[str]:
    ordered = [source for source in rule.source_priority if source in sources]
    ordered.extend(sorted(source for source in sources if source not in ordered))
    return ordered


def detect_conflicts(
    snapshots: list[Snapshot],
    rules: list[AttributeRule],
    display_names: dict[str, str] | None = None,
    source_names: dict[str, str] | None = None,
) -> list[DetectedConflict]:
    display_names = display_names or {}
    source_names = source_names or {}

    windows: dict[tuple[str, date], list[Snapshot]] = {}
    for row in snapshots:
        windows.setdefault((row.business_key, row.snapshot_date), []).append(row)

    detected: list[DetectedConflict] = []
    for (business_key, snapshot_date), rows in sorted(windows.items()):
        by_source: dict[str, Snapshot] = {}
        for row in rows:
            current = by_source.get(row.source_code)
            if current is None or row.ingested_at >= current.ingested_at:
                by_source[row.source_code] = row
        if len(by_source) < 2:
            continue

        for rule in rules:
            values: dict[str, tuple[str, Snapshot]] = {}
            for source_code, row in by_source.items():
                raw = row.attributes.get(rule.key)
                if raw is None or str(raw).strip() == "":
                    continue
                values[source_code] = (str(raw), row)
            if len(values) < 2:
                continue
            if len({raw for raw, _ in values.values()}) < 2:
                continue

            canonical = {
                source_code: canonical_value(rule.normalization, raw) for source_code, (raw, _) in values.items()
            }
            if len(set(canonical.values())) == 1:
                verdict = "normalized_equal"
                best_similarity = 1.0
                strategy = rule.normalization
            else:
                pairs = list(combinations(values.keys(), 2))
                best_similarity = max(
                    similarity(rule.normalization, values[a][0], values[b][0]) for a, b in pairs
                )
                if best_similarity >= SIMILARITY_THRESHOLD:
                    verdict = "similar"
                    strategy = "name_homophone"
                else:
                    verdict = "conflict"
                    strategy = None

            order = _priority_order(rule, set(values.keys()))
            winner = order[0]
            candidates = [
                Candidate(
                    source_code=source_code,
                    source_name=source_names.get(source_code, source_code),
                    value=values[source_code][0],
                    canonical=canonical[source_code],
                    observed_at=values[source_code][1].ingested_at,
                    trust=values[source_code][1].trust,
                )
                for source_code in order
            ]
            detected.append(
                DetectedConflict(
                    business_key=business_key,
                    snapshot_date=snapshot_date,
                    attribute_key=rule.key,
                    display_name=display_names.get(rule.key, rule.key),
                    candidates=candidates,
                    verdict=verdict,
                    similarity=best_similarity,
                    winner_source=winner,
                    winner_value=canonical[winner],
                    strategy=strategy,
                )
            )
    return detected


def dedupe_latest(items: list[DetectedConflict]) -> list[DetectedConflict]:
    """One conflict row per (business_key, attribute_key), keeping the latest window."""
    latest: dict[tuple[str, str], DetectedConflict] = {}
    for item in sorted(items, key=lambda entry: entry.snapshot_date):
        latest[(item.business_key, item.attribute_key)] = item
    return [latest[key] for key in sorted(latest)]


def overrides_from_resolutions(conflicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn human resolutions into SCD2 overrides effective the day after the window."""
    from datetime import timedelta

    overrides: list[dict[str, Any]] = []
    for conflict in conflicts:
        resolution = conflict.get("resolution") or {}
        strategy = resolution.get("strategy")
        if strategy not in ("candidate", "manual", "priority"):
            continue
        if not resolution.get("value"):
            continue
        window = conflict.get("snapshot_date")
        effective = window + timedelta(days=1) if isinstance(window, date) else None
        if effective is None:
            continue
        overrides.append(
            {
                "business_key": conflict["business_key"],
                "attribute_key": conflict["attribute_key"],
                "value": resolution["value"],
                "effective_date": effective,
                "conflict_id": conflict.get("id"),
                "note": resolution.get("note", ""),
            }
        )
    return overrides
