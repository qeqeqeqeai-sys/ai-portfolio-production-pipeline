from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash

ADVISORY_FLAGS: tuple[tuple[str, Any], ...] = (
    ("replay_mode", "advisory_only"),
    ("enforcement_enabled", False),
    ("canonical_override_enabled", False),
    ("scoring_mutation_enabled", False),
    ("propagation_mutation_enabled", False),
)


def stable_json_dumps(payload: Any) -> str:
    """Serialize dashboard/query payloads with deterministic field and list ordering."""
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": "))


def write_stable_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload), encoding="utf-8")


def advisory_contract() -> dict[str, Any]:
    return dict(ADVISORY_FLAGS)


def stable_row(row: dict[str, Any], field_order: Iterable[str] | None = None) -> dict[str, Any]:
    """Return an export-ready row with stable field order where practical."""
    ordered: OrderedDict[str, Any] = OrderedDict()
    for field in field_order or ():
        if field in row:
            ordered[field] = row[field]
    for key in sorted(row):
        if key not in ordered:
            ordered[key] = row[key]
    return dict(ordered)


def tabular_rows(rows: Iterable[dict[str, Any]], field_order: Iterable[str] | None = None) -> list[dict[str, Any]]:
    return [stable_row(row, field_order) for row in rows if isinstance(row, dict)]


def snapshot_payload(kind: str, rows: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "artifact_kind": kind,
        "row_count": len(rows),
        "rows": tabular_rows(rows),
        **advisory_contract(),
        **(metadata or {}),
    }
    payload["snapshot_hash"] = stable_hash(payload)
    return payload
