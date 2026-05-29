from __future__ import annotations

import json
from collections import OrderedDict
from decimal import Decimal
from hashlib import sha256
from numbers import Number
from typing import Any, Iterable, Mapping

MAX_PAYLOAD_BYTES = 8192
OBSERVATION_FACTS_TABLE = "sefi_observation_facts"
_REQUIRED_CONTEXT_FIELDS = ("phase_id", "phase_name", "artifact_id", "run_id")
_REQUIRED_ROW_FIELDS = (
    "phase_id",
    "phase_name",
    "entity_type",
    "entity_id",
    "metric_name",
    "artifact_id",
    "run_id",
    "payload_jsonb",
    "duplicate_prevention_key",
)


class ObservationFactEmissionError(ValueError):
    """Raised when a direct observation fact cannot be emitted safely."""


def _stable_string(value: Any, *, field_name: str, lowercase: bool = False, uppercase: bool = False) -> str:
    if value is None:
        raise ObservationFactEmissionError(f"{field_name} is required")
    normalized = " ".join(str(value).strip().split())
    if not normalized:
        raise ObservationFactEmissionError(f"{field_name} is required")
    if lowercase:
        normalized = normalized.lower()
    if uppercase:
        normalized = normalized.upper()
    return normalized


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _bounded_payload(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    if payload is None:
        payload = {}
    if not isinstance(payload, Mapping):
        raise ObservationFactEmissionError("payload_jsonb must be a mapping")
    ordered = OrderedDict((str(key), payload[key]) for key in sorted(payload, key=str))
    if len(_json_bytes(ordered)) > MAX_PAYLOAD_BYTES:
        raise ObservationFactEmissionError("payload_jsonb exceeds DB-1 bounded metadata limit")
    return ordered


def _validate_metric_value(metric_value: Any) -> int | float | Decimal | None:
    if metric_value is None:
        return None
    if isinstance(metric_value, bool) or not isinstance(metric_value, Number):
        raise ObservationFactEmissionError("metric_value must be numeric or null")
    return metric_value


def _duplicate_key(*parts: Any) -> str:
    normalized = "|".join("" if part is None else str(part) for part in (OBSERVATION_FACTS_TABLE, *parts))
    return sha256(normalized.encode("utf-8")).hexdigest()


def build_fact_emission_context(
    *,
    enabled: bool = False,
    dry_run: bool = True,
    phase_id: Any,
    phase_name: Any,
    artifact_id: Any,
    run_id: Any,
) -> OrderedDict[str, Any]:
    """Build the minimal gated context future phases pass into fact emission."""
    context = OrderedDict([
        ("enabled", bool(enabled)),
        ("dry_run", bool(dry_run)),
        ("phase_id", _stable_string(phase_id, field_name="phase_id")),
        ("phase_name", _stable_string(phase_name, field_name="phase_name")),
        ("artifact_id", _stable_string(artifact_id, field_name="artifact_id")),
        ("run_id", _stable_string(run_id, field_name="run_id")),
    ])
    return context


def should_emit_facts(context: Mapping[str, Any]) -> bool:
    """Return True only when the explicit emission gate and required context are present."""
    if not isinstance(context, Mapping) or context.get("enabled") is not True:
        return False
    return all(bool(str(context.get(field, "")).strip()) for field in _REQUIRED_CONTEXT_FIELDS)


def build_observation_fact_row(
    *,
    phase_id: Any,
    phase_name: Any,
    artifact_id: Any,
    run_id: Any,
    entity_type: Any,
    entity_id: Any,
    metric_name: Any,
    metric_value: Any = None,
    window_days: int | None = None,
    payload_jsonb: Mapping[str, Any] | None = None,
) -> OrderedDict[str, Any]:
    """Build one deterministic, append-only sefi_observation_facts insert row."""
    normalized_entity_type = _stable_string(entity_type, field_name="entity_type", lowercase=True)
    row = OrderedDict([
        ("phase_id", _stable_string(phase_id, field_name="phase_id")),
        ("phase_name", _stable_string(phase_name, field_name="phase_name")),
        ("window_days", window_days),
        ("entity_type", normalized_entity_type),
        ("entity_id", _stable_string(entity_id, field_name="entity_id", uppercase=normalized_entity_type == "symbol")),
        ("metric_name", _stable_string(metric_name, field_name="metric_name", lowercase=True)),
        ("metric_value", _validate_metric_value(metric_value)),
        ("artifact_id", _stable_string(artifact_id, field_name="artifact_id")),
        ("run_id", _stable_string(run_id, field_name="run_id")),
        ("payload_jsonb", _bounded_payload(payload_jsonb)),
    ])
    if window_days is not None and (isinstance(window_days, bool) or not isinstance(window_days, int)):
        raise ObservationFactEmissionError("window_days must be an integer or null")
    row["duplicate_prevention_key"] = _duplicate_key(
        row["phase_id"],
        row["phase_name"],
        row["window_days"],
        row["entity_type"],
        row["entity_id"],
        row["metric_name"],
        row["artifact_id"],
        row["run_id"],
    )
    validate_observation_fact_row(row)
    return row


def build_observation_fact_rows(*, context: Mapping[str, Any], observations: Iterable[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    """Build deterministic rows from a gated context and metric observations."""
    if not should_emit_facts(context):
        return []
    rows: list[OrderedDict[str, Any]] = []
    for observation in observations:
        rows.append(
            build_observation_fact_row(
                phase_id=context["phase_id"],
                phase_name=context["phase_name"],
                artifact_id=context["artifact_id"],
                run_id=context["run_id"],
                entity_type=observation.get("entity_type"),
                entity_id=observation.get("entity_id"),
                metric_name=observation.get("metric_name"),
                metric_value=observation.get("metric_value"),
                window_days=observation.get("window_days"),
                payload_jsonb=observation.get("payload_jsonb"),
            )
        )
    return rows


def validate_observation_fact_row(row: Mapping[str, Any]) -> bool:
    """Fail closed unless the row is a bounded append-only insert payload."""
    if not isinstance(row, Mapping):
        raise ObservationFactEmissionError("row must be a mapping")
    for field in _REQUIRED_ROW_FIELDS:
        if field not in row or (field != "payload_jsonb" and not str(row[field]).strip()):
            raise ObservationFactEmissionError(f"{field} is required")
    if row.get("window_days") is not None and (isinstance(row.get("window_days"), bool) or not isinstance(row.get("window_days"), int)):
        raise ObservationFactEmissionError("window_days must be an integer or null")
    _validate_metric_value(row.get("metric_value"))
    _bounded_payload(row.get("payload_jsonb"))
    expected_key = _duplicate_key(
        row["phase_id"],
        row["phase_name"],
        row.get("window_days"),
        row["entity_type"],
        row["entity_id"],
        row["metric_name"],
        row["artifact_id"],
        row["run_id"],
    )
    if row["duplicate_prevention_key"] != expected_key:
        raise ObservationFactEmissionError("duplicate_prevention_key is not deterministic for row identity")
    return True


def emit_observation_facts(client: Any, rows: Iterable[Mapping[str, Any]], dry_run: bool = True) -> OrderedDict[str, Any]:
    """Append observation facts through an injected client; dry-run is the safe default."""
    validated_rows = [OrderedDict(row) for row in rows]
    for row in validated_rows:
        validate_observation_fact_row(row)
    result = OrderedDict([
        ("table", OBSERVATION_FACTS_TABLE),
        ("dry_run", bool(dry_run)),
        ("attempted_rows", len(validated_rows)),
        ("inserted_rows", 0),
    ])
    if dry_run or not validated_rows:
        return result
    client.table(OBSERVATION_FACTS_TABLE).insert(validated_rows).execute()
    result["inserted_rows"] = len(validated_rows)
    return result
