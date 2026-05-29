from __future__ import annotations

import json
from collections import Counter, OrderedDict
from hashlib import sha256
from numbers import Number
from typing import Any, Iterable, Mapping, Sequence

from transmission_layers.history_read_model.fact_emitter import (
    MAX_PAYLOAD_BYTES,
    OBSERVATION_FACTS_TABLE,
    ObservationFactEmissionError,
    build_fact_emission_context,
    build_observation_fact_rows,
    emit_observation_facts,
)

PHASE_ID = "OPS-LIVE-2"
PHASE_NAME = "OPS-LIVE-2_controlled_live_observation_fact_accumulation"
SCHEMA_VERSION = "ops_live2_v1"
MAX_LOCAL_INPUT_ROWS = 1000
DEFAULT_RUN_ID = "ops-live2-local-dry-run"
DEFAULT_ARTIFACT_ID = "ops-live2-local-bounded-payload"
SUGGESTED_METRIC_NAMES = (
    "live_observation_value",
    "live_replay_density",
    "live_replay_saturation",
    "live_contradiction_burden",
    "live_sector_concentration",
    "live_subsector_concentration",
    "live_symbol_weakness",
    "live_provider_health",
    "live_ingestion_completeness",
)
_REQUIRED_LIVE_FIELDS = (
    "observed_at",
    "source_phase",
    "source_run_id",
    "entity_type",
    "entity_id",
    "metric_name",
    "metric_value",
)


def _stable_string(value: Any, field_name: str, *, lowercase: bool = False, uppercase: bool = False) -> str:
    if value is None:
        raise ObservationFactEmissionError(f"{field_name} is required")
    text = " ".join(str(value).strip().split())
    if not text:
        raise ObservationFactEmissionError(f"{field_name} is required")
    if lowercase:
        text = text.lower()
    if uppercase:
        text = text.upper()
    return text


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _ordered_mapping(payload: Mapping[str, Any] | None, *, field_name: str) -> OrderedDict[str, Any]:
    if payload is None:
        return OrderedDict()
    if not isinstance(payload, Mapping):
        raise ObservationFactEmissionError(f"{field_name} must be a mapping")
    ordered = OrderedDict((str(key), payload[key]) for key in sorted(payload, key=str))
    if len(_json_bytes(ordered)) > MAX_PAYLOAD_BYTES:
        raise ObservationFactEmissionError(f"{field_name} exceeds DB-1 bounded metadata limit")
    return ordered


def _metric_value(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Number):
        raise ObservationFactEmissionError("metric_value must be numeric or null")
    return value


def _window_days(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ObservationFactEmissionError("window_days must be an integer or null")
    return value


def _source_digest(observations: Sequence[Mapping[str, Any]]) -> str:
    encoded = json.dumps(list(observations), sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()[:16]


def build_ops_live2_context(
    observations: Sequence[Mapping[str, Any]] | None = None,
    *,
    enabled: bool = False,
    dry_run: bool = True,
    artifact_id: str | None = None,
    run_id: str | None = None,
) -> OrderedDict[str, Any]:
    """Build a deterministic, DB-2 gated context for OPS-LIVE-2 fact emission."""
    digest = _source_digest(observations or [])
    return build_fact_emission_context(
        enabled=enabled,
        dry_run=dry_run,
        phase_id=PHASE_ID,
        phase_name=PHASE_NAME,
        artifact_id=artifact_id or f"{DEFAULT_ARTIFACT_ID}-{digest}",
        run_id=run_id or f"{DEFAULT_RUN_ID}-{digest}",
    )


def normalize_live_observation(observation: Mapping[str, Any]) -> OrderedDict[str, Any]:
    """Normalize one bounded live observation into a DB-2 observation payload."""
    if not isinstance(observation, Mapping):
        raise ObservationFactEmissionError("live observation must be a mapping")
    for field in _REQUIRED_LIVE_FIELDS:
        if field not in observation:
            raise ObservationFactEmissionError(f"{field} is required")

    entity_type = _stable_string(observation.get("entity_type"), "entity_type", lowercase=True)
    payload = _ordered_mapping(observation.get("payload_jsonb"), field_name="payload_jsonb")
    payload["observed_at"] = _stable_string(observation.get("observed_at"), "observed_at")
    payload["schema_version"] = SCHEMA_VERSION
    payload["source_phase"] = _stable_string(observation.get("source_phase"), "source_phase")
    payload["source_run_id"] = _stable_string(observation.get("source_run_id"), "source_run_id")
    payload = _ordered_mapping(payload, field_name="payload_jsonb")

    return OrderedDict([
        ("entity_type", entity_type),
        ("entity_id", _stable_string(observation.get("entity_id"), "entity_id", uppercase=entity_type == "symbol")),
        ("metric_name", _stable_string(observation.get("metric_name"), "metric_name", lowercase=True)),
        ("metric_value", _metric_value(observation.get("metric_value"))),
        ("window_days", _window_days(observation.get("window_days"))),
        ("payload_jsonb", payload),
    ])


def build_ops_live2_observations(live_observations: Iterable[Mapping[str, Any]], *, max_rows: int = MAX_LOCAL_INPUT_ROWS) -> list[OrderedDict[str, Any]]:
    """Normalize at most max_rows live observations deterministically."""
    rows: list[OrderedDict[str, Any]] = []
    for index, observation in enumerate(live_observations):
        if index >= max_rows:
            break
        rows.append(normalize_live_observation(observation))
    return rows


def build_ops_live2_fact_rows(
    live_observations: Iterable[Mapping[str, Any]],
    *,
    enabled: bool = False,
    dry_run: bool = True,
    artifact_id: str | None = None,
    run_id: str | None = None,
    max_rows: int = MAX_LOCAL_INPUT_ROWS,
) -> list[OrderedDict[str, Any]]:
    observations = build_ops_live2_observations(live_observations, max_rows=max_rows)
    context = build_ops_live2_context(observations, enabled=enabled, dry_run=dry_run, artifact_id=artifact_id, run_id=run_id)
    return build_observation_fact_rows(context=context, observations=observations)


def _default_emission_result(dry_run: bool = True) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("table", OBSERVATION_FACTS_TABLE),
        ("dry_run", bool(dry_run)),
        ("attempted_rows", 0),
        ("inserted_rows", 0),
    ])


def _input_source_summary(input_source: str | None, raw_count: int, normalized_count: int, max_rows: int) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("input_source", input_source or "local_synthetic_payload"),
        ("raw_observation_count", raw_count),
        ("max_rows", max_rows),
        ("normalized_observation_count", normalized_count),
        ("truncated", raw_count > max_rows),
    ])


def run_ops_live2_accumulation(
    *,
    live_observations: Iterable[Mapping[str, Any]],
    client: Any | None = None,
    enabled: bool = False,
    dry_run: bool = True,
    artifact_id: str | None = None,
    run_id: str | None = None,
    input_source: str | None = None,
    max_rows: int = MAX_LOCAL_INPUT_ROWS,
    raw_observation_count: int | None = None,
) -> OrderedDict[str, Any]:
    raw = list(live_observations)
    observations = build_ops_live2_observations(raw, max_rows=max_rows)
    context = build_ops_live2_context(observations, enabled=enabled, dry_run=dry_run, artifact_id=artifact_id, run_id=run_id)
    fact_rows = build_observation_fact_rows(context=context, observations=observations)
    can_write = enabled is True and dry_run is False and client is not None
    emission = emit_observation_facts(client, fact_rows, dry_run=False) if can_write else _default_emission_result(dry_run=True)
    if enabled and dry_run:
        emission = emit_observation_facts(client, fact_rows, dry_run=True)
    report_model = OrderedDict([
        ("context", context),
        ("input_source_summary", _input_source_summary(input_source, raw_observation_count if raw_observation_count is not None else len(raw), len(observations), max_rows)),
        ("normalized_observation_count", len(observations)),
        ("fact_row_count", len(fact_rows)),
        ("metric_counts", OrderedDict(sorted(Counter(row["metric_name"] for row in observations).items()))),
        ("enabled", bool(enabled)),
        ("dry_run", bool(dry_run) or not can_write),
        ("fact_emission", emission),
        ("governance_review", OrderedDict([
            ("consumes_bounded_existing_observations", True),
            ("provider_api_calls_enabled", False),
            ("fmp_calls_enabled", False),
            ("live_ingestion_enabled", False),
            ("prediction_enabled", False),
            ("trading_execution_enabled", False),
            ("replay_execution_enabled", False),
            ("topology_persistence_enabled", False),
            ("schema_changes_enabled", False),
            ("core_supabase_client_creation_enabled", False),
        ])),
    ])
    return OrderedDict([
        ("context", context),
        ("observations", observations),
        ("fact_rows", fact_rows),
        ("fact_emission", emission),
        ("report", build_ops_live2_report(report_model)),
        ("report_model", report_model),
    ])


def _line(text: str = "") -> str:
    return f"{text}\n"


def build_ops_live2_report(result: Mapping[str, Any]) -> str:
    model = result.get("report_model", result) if isinstance(result, Mapping) else {}
    source = model.get("input_source_summary") or {}
    metric_counts = model.get("metric_counts") or {}
    governance = model.get("governance_review") or {}
    emission = model.get("fact_emission") or {}
    lines = [
        _line("# OPS-LIVE-2 Controlled Live Observation Fact Accumulation"),
        _line("## Objective"),
        _line("Convert bounded, already-produced live observation outputs into normalized DB-2 observation facts for sefi_observation_facts."),
        _line("## Input Source Summary"),
        _line(f"- Source: {source.get('input_source', 'local_synthetic_payload')}"),
        _line(f"- Raw observations: {source.get('raw_observation_count', 0)}"),
        _line(f"- Max accepted rows: {source.get('max_rows', MAX_LOCAL_INPUT_ROWS)}"),
        _line(f"- Truncated: {source.get('truncated', False)}"),
        _line("## Normalized Observation Counts"),
        _line(f"- Normalized observations: {model.get('normalized_observation_count', 0)}"),
        _line("## Fact-Row Counts"),
        _line(f"- DB-2 fact rows: {model.get('fact_row_count', 0)}"),
        _line("## Dry-Run / Write Mode"),
        _line(f"- Enabled: {model.get('enabled', False)}"),
        _line(f"- Dry run: {model.get('dry_run', True)}"),
        _line(f"- Attempted rows: {emission.get('attempted_rows', 0)}"),
        _line(f"- Inserted rows: {emission.get('inserted_rows', 0)}"),
        _line("## Sample Metric Names"),
    ]
    sample_metrics = list(metric_counts.keys())[:10] or list(SUGGESTED_METRIC_NAMES[:5])
    for metric in sample_metrics:
        suffix = f" count={metric_counts[metric]}" if metric in metric_counts else ""
        lines.append(_line(f"- {metric}{suffix}"))
    lines.extend([
        _line("## Governance Review"),
    ])
    for key, value in governance.items():
        lines.append(_line(f"- {key}: {value}"))
    lines.extend([
        _line("## Limitations"),
        _line("- Accumulation-only phase; it depends on upstream bounded observation payloads and does not validate provider completeness."),
        _line("- No topology persistence, prediction, trading, replay execution, market-data fetching, or schema migration is performed."),
        _line("## Next-Step Recommendation"),
        _line("- After dry-run review, enable DB-2 insertion only with an injected Supabase client and explicit write flags."),
    ])
    return "".join(lines)
