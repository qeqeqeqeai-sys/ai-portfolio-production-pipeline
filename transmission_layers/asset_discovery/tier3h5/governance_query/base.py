from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import load_json

DEFAULT_LIMIT = 100
MAX_LIMIT = 500
DEFAULT_WINDOW = 100

STATUS_FIELDS = {
    "governance_status": ("governance_status", "historical_governance_status", "replay_governance_status"),
    "trend_status": ("governance_trend_status",),
    "escalation_status": ("escalation_status",),
    "continuity_status": ("continuity_status", "historical_continuity_status"),
    "registry_source": ("registry_source", "source_registry", "registry"),
    "entity_id": ("entity_id", "entity", "canonical_entity_id", "canonical_security_id", "canonical_issuer_id"),
    "governance_domain": ("governance_domain", "category"),
}
DATE_FIELDS = ("run_date_sgt", "run_date", "archived_at_sgt", "created_at", "event_timestamp")


def history_rows(path: Path, key: str = "history") -> list[dict[str, Any]]:
    payload = load_json(path)
    rows = payload.get(key, [])
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def stable_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    preferred = row.get("run_date_sgt") or row.get("run_date") or row.get("archived_at_sgt") or ""
    encoded = json.dumps(row, sort_keys=True, separators=(",", ":"))
    return str(preferred), encoded


def stable_sort(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted([row for row in rows if isinstance(row, dict)], key=stable_sort_key)


def bounded_window(rows: list[dict[str, Any]], window: int | None = None) -> list[dict[str, Any]]:
    limit = DEFAULT_WINDOW if window is None else max(0, min(int(window), MAX_LIMIT))
    ordered = stable_sort(rows)
    return ordered[-limit:] if limit else []


def _exact_match(row: dict[str, Any], fields: tuple[str, ...], expected: Any) -> bool:
    if expected is None:
        return True
    values = {str(row.get(field)) for field in fields if field in row}
    if isinstance(expected, (set, list, tuple)):
        expected_values = {str(value) for value in expected}
        return bool(values & expected_values)
    return str(expected) in values


def _date_value(row: dict[str, Any]) -> str:
    for field in DATE_FIELDS:
        if row.get(field) is not None:
            return str(row[field])
    return ""


def apply_filters(
    rows: list[dict[str, Any]],
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    governance_status: Any = None,
    trend_status: Any = None,
    escalation_status: Any = None,
    continuity_status: Any = None,
    registry_source: Any = None,
    entity_id: Any = None,
    governance_domain: Any = None,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    exact_filters = {
        "governance_status": governance_status,
        "trend_status": trend_status,
        "escalation_status": escalation_status,
        "continuity_status": continuity_status,
        "registry_source": registry_source,
        "entity_id": entity_id,
        "governance_domain": governance_domain,
    }
    for row in rows:
        date_value = _date_value(row)
        if start_date and date_value and date_value < start_date:
            continue
        if end_date and date_value and date_value > end_date:
            continue
        if all(_exact_match(row, STATUS_FIELDS[name], value) for name, value in exact_filters.items()):
            filtered.append(row)
    return stable_sort(filtered)


def paginate(rows: list[dict[str, Any]], *, page: int = 1, page_size: int = DEFAULT_LIMIT) -> dict[str, Any]:
    safe_page = max(1, int(page))
    safe_size = max(1, min(int(page_size), MAX_LIMIT))
    ordered = stable_sort(rows)
    start = (safe_page - 1) * safe_size
    end = start + safe_size
    return {
        "page": safe_page,
        "page_size": safe_size,
        "total_rows": len(ordered),
        "rows": ordered[start:end],
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
