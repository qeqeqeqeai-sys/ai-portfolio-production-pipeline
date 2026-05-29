from __future__ import annotations

from collections import Counter, OrderedDict
from hashlib import sha256
import json
from numbers import Number
from typing import Any, Iterable, Mapping, Sequence

from transmission_layers.history_read_model.observation_query import (
    DEFAULT_LIMIT,
    MAX_LOCAL_ROWS,
    OBSERVATION_FACTS_TABLE,
    get_observation_fact_summary,
)

PHASE_ID = "OPS-LIVE-3"
PHASE_NAME = "OPS-LIVE-3_live_structural_state_snapshot"
SCHEMA_VERSION = "ops_live3_v1"
MAX_FACT_ROWS = MAX_LOCAL_ROWS
LIVE2_PHASE_ID = "OPS-LIVE-2"
LIVE_METRIC_PREFIX = "live_"
CLASS_HEALTHY = "HEALTHY"
CLASS_WATCH = "WATCH"
CLASS_DEGRADED = "DEGRADED"
CLASS_INSUFFICIENT = "INSUFFICIENT_DATA"
CLASS_ORDER = {
    CLASS_HEALTHY: 0,
    CLASS_WATCH: 1,
    CLASS_DEGRADED: 2,
    CLASS_INSUFFICIENT: 3,
}
READ_COLUMNS = (
    "phase_id,phase_name,window_days,entity_type,entity_id,metric_name,metric_value,"
    "artifact_id,run_id,loaded_at,payload_jsonb"
)
LIVE_METRIC_NAMES = {
    "live_ingestion_completeness",
    "live_provider_health",
    "live_symbol_weakness",
    "live_replay_density",
    "live_replay_saturation",
    "live_contradiction_burden",
    "live_sector_concentration",
    "live_subsector_concentration",
}


def _bounded_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    return max(0, min(int(limit), MAX_FACT_ROWS))


def _execute(query: Any) -> Any:
    result = query.execute()
    return getattr(result, "data", result)


def _query_live_fact_rows(client: Any, *, limit: int = DEFAULT_LIMIT) -> list[Mapping[str, Any]]:
    query = client.table(OBSERVATION_FACTS_TABLE).select(READ_COLUMNS)
    query = query.order("loaded_at", desc=True).limit(_bounded_limit(limit))
    rows = _execute(query) or []
    return [row for row in rows if isinstance(row, Mapping) and _is_live_fact(row)]


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb")
    return payload if isinstance(payload, Mapping) else {}


def _metric_name(row: Mapping[str, Any]) -> str:
    return str(row.get("metric_name") or "").strip().lower()


def _is_live_fact(row: Mapping[str, Any]) -> bool:
    metric = _metric_name(row)
    return metric.startswith(LIVE_METRIC_PREFIX) or str(row.get("phase_id") or "").strip() == LIVE2_PHASE_ID


def _usable_live_fact(row: Mapping[str, Any]) -> bool:
    return bool(_metric_name(row)) and _is_live_fact(row)


def _local_live_fact_rows(fact_rows: Iterable[Mapping[str, Any]] | None, *, limit: int) -> list[Mapping[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    for row in fact_rows or []:
        if not isinstance(row, Mapping):
            continue
        if _usable_live_fact(row):
            selected.append(row)
        if len(selected) >= _bounded_limit(limit):
            break
    return sorted(selected, key=_row_sort_key)


def _row_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _observed_at(row),
        str(row.get("run_id") or _payload(row).get("source_run_id") or ""),
        _metric_name(row),
        str(row.get("entity_id") or ""),
    )


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, Number):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = _payload(row)
    for key in ("value", "score", "metric_value"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _observed_at(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    for key in ("observed_at", "loaded_at", "created_at", "completed_at"):
        value = payload.get(key) if key == "observed_at" else row.get(key)
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _source_run_id(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    return str(payload.get("source_run_id") or row.get("run_id") or "").strip()


def _classify_positive(value: float | None) -> str:
    if value is None:
        return CLASS_INSUFFICIENT
    if value >= 0.95:
        return CLASS_HEALTHY
    if value >= 0.80:
        return CLASS_WATCH
    return CLASS_DEGRADED


def _classify_pressure(value: float | None) -> str:
    if value is None:
        return CLASS_INSUFFICIENT
    if value <= 0.25:
        return CLASS_HEALTHY
    if value <= 0.50:
        return CLASS_WATCH
    return CLASS_DEGRADED


def _worst_class(classes: Iterable[str]) -> str:
    values = [klass for klass in classes if klass in CLASS_ORDER]
    if not values:
        return CLASS_INSUFFICIENT
    return max(values, key=lambda klass: CLASS_ORDER[klass])


def _latest_values_by_metric(rows: Sequence[Mapping[str, Any]]) -> OrderedDict[str, float | None]:
    latest: dict[str, tuple[tuple[str, str, str, str], float | None]] = {}
    for row in rows:
        metric = _metric_name(row)
        if metric not in LIVE_METRIC_NAMES:
            continue
        key = _row_sort_key(row)
        if metric not in latest or key >= latest[metric][0]:
            latest[metric] = (key, _metric_value(row))
    return OrderedDict((metric, _round(latest[metric][1]) if metric in latest else None) for metric in sorted(LIVE_METRIC_NAMES))


def _source_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    return sha256(json.dumps(list(rows), sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _insufficient_rows(rows: Sequence[Mapping[str, Any]]) -> int:
    count = 0
    for row in rows:
        payload = _payload(row)
        if _metric_value(row) is None or str(payload.get("stability_class") or payload.get("health_class") or "") == CLASS_INSUFFICIENT:
            count += 1
    return count


def _governance_review() -> OrderedDict[str, bool]:
    return OrderedDict([
        ("fmp_calls_enabled", False),
        ("provider_api_calls_enabled", False),
        ("live_ingestion_enabled", False),
        ("replay_execution_enabled", False),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("artifact_mutation_enabled", False),
        ("fact_emission_enabled", False),
        ("schema_changes_enabled", False),
        ("destructive_database_operations_enabled", False),
        ("core_supabase_client_creation_enabled", False),
    ])


def build_ops_live3_snapshot(
    *,
    client: Any | None = None,
    fact_rows: Iterable[Mapping[str, Any]] | None = None,
    limit: int = DEFAULT_LIMIT,
) -> OrderedDict[str, Any]:
    """Build a deterministic read-only live structural state snapshot from observation facts."""
    rows = _query_live_fact_rows(client, limit=limit) if client is not None else _local_live_fact_rows(fact_rows, limit=limit)
    rows = sorted(rows[: _bounded_limit(limit)], key=_row_sort_key)
    summary = get_observation_fact_summary(fact_rows=rows, limit=limit)
    latest_values = _latest_values_by_metric(rows)
    insufficient_count = _insufficient_rows(rows)
    latest_observed_at = max((_observed_at(row) for row in rows), default="") or None
    entities = {f"{row.get('entity_type') or ''}:{row.get('entity_id') or ''}" for row in rows if row.get("entity_id")}
    source_runs = {_source_run_id(row) for row in rows if _source_run_id(row)}
    metrics_present = {metric for metric, value in latest_values.items() if value is not None}

    ingestion_class = _classify_positive(latest_values.get("live_ingestion_completeness"))
    provider_class = _classify_positive(latest_values.get("live_provider_health"))
    weakness_class = _classify_pressure(latest_values.get("live_symbol_weakness"))
    replay_pressure = max(
        (value for value in (latest_values.get("live_replay_density"), latest_values.get("live_replay_saturation")) if value is not None),
        default=None,
    )
    replay_class = _classify_pressure(replay_pressure)
    contradiction_class = _classify_pressure(latest_values.get("live_contradiction_burden"))
    concentration_pressure = max(
        (value for value in (latest_values.get("live_sector_concentration"), latest_values.get("live_subsector_concentration")) if value is not None),
        default=None,
    )
    concentration_class = _classify_pressure(concentration_pressure)
    dimension_classes = OrderedDict([
        ("live_ingestion_completeness", ingestion_class),
        ("live_provider_health", provider_class),
        ("live_symbol_weakness", weakness_class),
        ("live_replay_density", _classify_pressure(latest_values.get("live_replay_density"))),
        ("live_replay_saturation", _classify_pressure(latest_values.get("live_replay_saturation"))),
        ("live_contradiction_burden", contradiction_class),
        ("live_sector_concentration", _classify_pressure(latest_values.get("live_sector_concentration"))),
        ("live_subsector_concentration", _classify_pressure(latest_values.get("live_subsector_concentration"))),
    ])
    live_health_class = _worst_class(dimension_classes.values())
    if not rows or not metrics_present:
        live_health_class = CLASS_INSUFFICIENT

    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("phase_id", PHASE_ID),
        ("source_table", OBSERVATION_FACTS_TABLE),
        ("source_behavior", OBSERVATION_FACTS_TABLE if client is not None else "bounded_local_fact_rows"),
        ("snapshot_status", "INSUFFICIENT_DATA" if live_health_class == CLASS_INSUFFICIENT else "BUILT"),
        ("live_health_class", live_health_class),
        ("ingestion_completeness_class", ingestion_class),
        ("provider_health_class", provider_class),
        ("weakness_pressure_class", weakness_class),
        ("replay_pressure_class", replay_class),
        ("contradiction_pressure_class", contradiction_class),
        ("concentration_pressure_class", concentration_class),
        ("entity_coverage_count", len(entities)),
        ("source_run_count", len(source_runs)),
        ("insufficient_data_count", insufficient_count + sum(1 for value in latest_values.values() if value is None)),
        ("latest_observed_at", latest_observed_at),
        ("inspected_fact_count", len(rows)),
        ("metric_coverage_count", len(metrics_present)),
        ("metric_values", latest_values),
        ("dimension_classifications", dimension_classes),
        ("entity_coverage", sorted(entities)),
        ("source_run_coverage", sorted(source_runs)),
        ("metric_counts", OrderedDict(sorted(Counter(_metric_name(row) for row in rows).items()))),
        ("observation_fact_summary", summary),
        ("source_digest", _source_digest(rows)),
        ("governance_review", _governance_review()),
    ])


def build_ops_live3_state_summary(snapshot: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("snapshot_status", snapshot.get("snapshot_status")),
        ("live_health_class", snapshot.get("live_health_class")),
        ("ingestion_completeness_class", snapshot.get("ingestion_completeness_class")),
        ("provider_health_class", snapshot.get("provider_health_class")),
        ("weakness_pressure_class", snapshot.get("weakness_pressure_class")),
        ("replay_pressure_class", snapshot.get("replay_pressure_class")),
        ("contradiction_pressure_class", snapshot.get("contradiction_pressure_class")),
        ("concentration_pressure_class", snapshot.get("concentration_pressure_class")),
        ("entity_coverage_count", snapshot.get("entity_coverage_count")),
        ("source_run_count", snapshot.get("source_run_count")),
        ("insufficient_data_count", snapshot.get("insufficient_data_count")),
        ("latest_observed_at", snapshot.get("latest_observed_at")),
    ])


def build_ops_live3_report(snapshot: Mapping[str, Any]) -> str:
    summary = build_ops_live3_state_summary(snapshot)
    facts = snapshot.get("observation_fact_summary") or {}
    lines = [
        "# OPS-LIVE-3 Live Structural State Snapshot\n",
        "## Objective\n",
        "Synthesize accumulated live observation facts into a bounded ecosystem-state snapshot without ingestion, replay, prediction, trading, topology mutation, or fact emission.\n",
        "## Source Behavior\n",
        f"- source_table: {snapshot.get('source_table')}\n",
        f"- source_behavior: {snapshot.get('source_behavior')}\n",
        "- source_input_policy: fact-native sefi_observation_facts rows or bounded local fact rows only; markdown reports and large JSON artifacts are not source inputs.\n",
        "## Inspected Fact Source Summary\n",
        f"- inspected_fact_count: {snapshot.get('inspected_fact_count')}\n",
        f"- metric_coverage_count: {snapshot.get('metric_coverage_count')}\n",
        f"- source_digest: {snapshot.get('source_digest')}\n",
        f"- obs_query_row_count: {facts.get('row_count')}\n",
        "## Live Structural State Summary\n",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}\n")
    lines.append("## Dimension Classifications\n")
    for key, value in (snapshot.get("dimension_classifications") or {}).items():
        metric_value = (snapshot.get("metric_values") or {}).get(key)
        lines.append(f"- {key}: class={value} value={metric_value}\n")
    lines.extend([
        "## Entity/Source Coverage\n",
        f"- entity_coverage_count: {snapshot.get('entity_coverage_count')}\n",
        f"- source_run_count: {snapshot.get('source_run_count')}\n",
        "## Insufficient-Data Review\n",
        f"- insufficient_data_count: {snapshot.get('insufficient_data_count')}\n",
        f"- snapshot_status: {snapshot.get('snapshot_status')}\n",
        "## Governance Review\n",
    ])
    for key, value in (snapshot.get("governance_review") or {}).items():
        lines.append(f"- {key}: {value}\n")
    lines.extend([
        "## Limitations\n",
        "- This synthesis is bounded by available live observation facts and does not validate external market truth.\n",
        "- Missing live metrics fail closed as INSUFFICIENT_DATA.\n",
        "## Next-Step Recommendation\n",
        "- Continue read-only monitoring of OPS-LIVE-2/live_* fact coverage before any future governed emission or persistence phase.\n",
    ])
    return "".join(lines)


def run_ops_live3_snapshot(
    *,
    client: Any | None = None,
    fact_rows: Iterable[Mapping[str, Any]] | None = None,
    limit: int = DEFAULT_LIMIT,
) -> OrderedDict[str, Any]:
    snapshot = build_ops_live3_snapshot(client=client, fact_rows=fact_rows, limit=limit)
    return OrderedDict([
        ("snapshot", snapshot),
        ("summary", build_ops_live3_state_summary(snapshot)),
        ("report", build_ops_live3_report(snapshot)),
    ])
