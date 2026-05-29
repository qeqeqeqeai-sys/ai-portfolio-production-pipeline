from __future__ import annotations

import json
from collections import Counter, OrderedDict, defaultdict
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

OBSERVATION_FACTS_TABLE = "sefi_observation_facts"
DEFAULT_LIMIT = 500
MAX_LOCAL_ROWS = 1000
STABILITY_SCORE = {"INSUFFICIENT_DATA": 0, "VOLATILE": 1, "PARTIALLY_STABLE": 2, "STABLE": 3}
DRIFT_SEVERITY = {"DETERIORATING": 3, "MIXED": 2, "STABLE": 1, "IMPROVING": 0, "INSUFFICIENT_DATA": -1}

_READ_COLUMNS = (
    "phase_id,phase_name,window_days,entity_type,entity_id,metric_name,metric_value,"
    "artifact_id,run_id,loaded_at,payload_jsonb"
)


def _execute(query: Any) -> Any:
    result = query.execute()
    return getattr(result, "data", result)


def _query_fact_rows(
    client: Any,
    *,
    phase_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metric_name: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[Mapping[str, Any]]:
    query = client.table(OBSERVATION_FACTS_TABLE).select(_READ_COLUMNS)
    if phase_id is not None:
        query = query.eq("phase_id", phase_id)
    if entity_type is not None:
        query = query.eq("entity_type", entity_type)
    if entity_id is not None:
        query = query.eq("entity_id", entity_id)
    if metric_name is not None:
        query = query.eq("metric_name", metric_name)
    query = query.order("loaded_at", desc=True).limit(_bounded_limit(limit))
    return [row for row in (_execute(query) or []) if isinstance(row, Mapping)]


def _bounded_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    return max(0, min(int(limit), MAX_LOCAL_ROWS))


def _rows(
    *,
    client: Any | None = None,
    fact_rows: Iterable[Mapping[str, Any]] | None = None,
    phase_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metric_name: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[Mapping[str, Any]]:
    if client is not None:
        return _query_fact_rows(
            client,
            phase_id=phase_id,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            limit=limit,
        )
    selected: list[Mapping[str, Any]] = []
    for row in fact_rows or []:
        if not isinstance(row, Mapping):
            continue
        if phase_id is not None and row.get("phase_id") != phase_id:
            continue
        if entity_type is not None and row.get("entity_type") != entity_type:
            continue
        if entity_id is not None and row.get("entity_id") != entity_id:
            continue
        if metric_name is not None and row.get("metric_name") != metric_name:
            continue
        selected.append(row)
        if len(selected) >= _bounded_limit(limit):
            break
    return sorted(selected, key=lambda row: (_time_key(row), str(row.get("run_id", "")), str(row.get("metric_name", ""))))


def _time_key(row: Mapping[str, Any]) -> str:
    return str(row.get("loaded_at") or row.get("created_at") or row.get("completed_at") or row.get("run_id") or "")


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb")
    return payload if isinstance(payload, Mapping) else {}


def _dimension(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    for key in ("dimension", "structure", "morphology", "stability_dimension"):
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    entity_id = str(row.get("entity_id", "")).strip()
    if ":" in entity_id:
        return entity_id.rsplit(":", 1)[-1]
    return entity_id or str(row.get("metric_name", "unknown"))


def _stability_class(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    return str(payload.get("stability_class") or payload.get("stability_class_transition") or "INSUFFICIENT_DATA")


def _metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = _payload(row)
    for key in ("persistence_score", "score", "value", "emerging_fragility_score"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _snapshot_id(row: Mapping[str, Any], index: int = 0) -> str:
    for key in ("loaded_at", "run_id", "artifact_id"):
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return f"snapshot_{index:04d}"


def _source_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    return sha256(json.dumps(list(rows), sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _governance_review() -> OrderedDict[str, bool]:
    return OrderedDict([
        ("fmp_calls_enabled", False),
        ("provider_api_calls_enabled", False),
        ("live_ingestion_enabled", False),
        ("replay_execution_enabled", False),
        ("prediction_enabled", False),
        ("trading_execution_enabled", False),
        ("topology_persistence_enabled", False),
        ("fact_emission_enabled", False),
        ("schema_changes_enabled", False),
        ("destructive_database_operations_enabled", False),
    ])


def get_observation_fact_summary(*, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, phase_id: str | None = None, limit: int = DEFAULT_LIMIT) -> OrderedDict[str, Any]:
    rows = _rows(client=client, fact_rows=fact_rows, phase_id=phase_id, limit=limit)
    phase_counts = Counter(str(row.get("phase_id", "unknown")) for row in rows)
    metric_counts = Counter(str(row.get("metric_name", "unknown")) for row in rows)
    insufficient = sum(1 for row in rows if _metric_value(row) is None or _stability_class(row) == "INSUFFICIENT_DATA")
    return OrderedDict([
        ("source", OBSERVATION_FACTS_TABLE if client is not None else "bounded_local_observation_facts"),
        ("row_count", len(rows)),
        ("phase_counts", OrderedDict(sorted(phase_counts.items()))),
        ("metric_counts", OrderedDict(sorted(metric_counts.items()))),
        ("snapshot_count", len({_snapshot_id(row, index) for index, row in enumerate(rows)})),
        ("insufficient_data_count", insufficient),
        ("source_digest", _source_digest(rows)),
    ])


def get_metric_series(*, metric_name: str, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, phase_id: str | None = None, entity_id: str | None = None, limit: int = DEFAULT_LIMIT) -> list[OrderedDict[str, Any]]:
    rows = sorted(
        _rows(client=client, fact_rows=fact_rows, phase_id=phase_id, entity_id=entity_id, metric_name=metric_name, limit=limit),
        key=lambda row: (_time_key(row), str(row.get("run_id", "")), str(row.get("metric_name", ""))),
    )
    series = []
    for index, row in enumerate(rows):
        series.append(OrderedDict([
            ("snapshot_id", _snapshot_id(row, index)),
            ("loaded_at", _time_key(row)),
            ("phase_id", row.get("phase_id")),
            ("entity_type", row.get("entity_type")),
            ("entity_id", row.get("entity_id")),
            ("metric_name", row.get("metric_name")),
            ("metric_value", _round(_metric_value(row))),
            ("dimension", _dimension(row)),
            ("stability_class", _stability_class(row)),
        ]))
    return series


def get_latest_metric_snapshot(*, metric_name: str, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, phase_id: str | None = None, limit: int = DEFAULT_LIMIT) -> OrderedDict[str, Any]:
    series = get_metric_series(metric_name=metric_name, client=client, fact_rows=fact_rows, phase_id=phase_id, limit=limit)
    latest = series[-1] if series else None
    return OrderedDict([("metric_name", metric_name), ("latest", latest), ("available", latest is not None)])


def get_top_persistent_structures(*, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, limit: int = 10) -> list[OrderedDict[str, Any]]:
    rows = _rows(client=client, fact_rows=fact_rows, limit=MAX_LOCAL_ROWS)
    candidates = []
    for row in rows:
        payload = _payload(row)
        if row.get("metric_name") in {"persistence_score", "overall_persistence_score"} or "persistence_score" in payload:
            score = _metric_value(row)
            if score is None:
                continue
            candidates.append((_round(score), _dimension(row), row))
    ranked = sorted(candidates, key=lambda item: (-(item[0] or 0), item[1], _time_key(item[2])))[: _bounded_limit(limit)]
    return [OrderedDict([("structure", dim), ("persistence_score", score), ("stability_class", _stability_class(row)), ("phase_id", row.get("phase_id"))]) for score, dim, row in ranked]


def get_top_deteriorating_metrics(*, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, limit: int = 10) -> list[OrderedDict[str, Any]]:
    rows = _rows(client=client, fact_rows=fact_rows, limit=MAX_LOCAL_ROWS)
    candidates = []
    for row in rows:
        payload = _payload(row)
        drift = str(payload.get("drift_class") or row.get("drift_class") or "")
        delta = _metric_value(row)
        if drift == "DETERIORATING" or (delta is not None and delta < 0):
            candidates.append((DRIFT_SEVERITY.get(drift, 0), delta if delta is not None else 0.0, str(row.get("metric_name", "")), row))
    ranked = sorted(candidates, key=lambda item: (-item[0], item[1], item[2]))[: _bounded_limit(limit)]
    return [OrderedDict([("metric_name", row.get("metric_name")), ("entity_id", row.get("entity_id")), ("score_delta", _round(_metric_value(row))), ("drift_class", _payload(row).get("drift_class"))]) for _, __, ___, row in ranked]


def get_fragility_leaderboard(*, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, limit: int = 10) -> list[OrderedDict[str, Any]]:
    rows = _rows(client=client, fact_rows=fact_rows, metric_name="emerging_fragility_score", limit=MAX_LOCAL_ROWS)
    ranked = sorted([( _metric_value(row), row) for row in rows if _metric_value(row) is not None], key=lambda item: (-(item[0] or 0), str(item[1].get("entity_id", ""))))[: _bounded_limit(limit)]
    return [OrderedDict([("entity_id", row.get("entity_id")), ("emerging_fragility_score", _round(score)), ("emerging_fragility_class", _payload(row).get("emerging_fragility_class")), ("phase_id", row.get("phase_id"))]) for score, row in ranked]


def get_morphology_recurrence(*, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, limit: int = 10) -> list[OrderedDict[str, Any]]:
    rows = _rows(client=client, fact_rows=fact_rows, limit=MAX_LOCAL_ROWS)
    counter: Counter[str] = Counter()
    windows: dict[str, set[Any]] = defaultdict(set)
    for index, row in enumerate(rows):
        payload = _payload(row)
        structures = payload.get("recurring_structures") or payload.get("morphologies") or []
        if isinstance(structures, str):
            structures = [structures]
        if not isinstance(structures, Sequence):
            structures = []
        if not structures and "morphology" in str(row.get("metric_name", "")):
            structures = [_dimension(row)]
        for structure in sorted({str(item).strip().lower() for item in structures if str(item).strip()}):
            counter[structure] += 1
            windows[structure].add(row.get("window_days") or _snapshot_id(row, index))
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[: _bounded_limit(limit)]
    return [OrderedDict([("morphology", key), ("recurrence_count", count), ("distinct_windows_or_snapshots", len(windows[key]))]) for key, count in ranked]


def get_stability_transition_summary(*, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, limit: int = DEFAULT_LIMIT) -> OrderedDict[str, Any]:
    rows = _rows(client=client, fact_rows=fact_rows, limit=limit)
    transitions: Counter[str] = Counter()
    insufficient = 0
    trend_counts: Counter[str] = Counter()
    for row in rows:
        payload = _payload(row)
        transition = str(payload.get("stability_class_transition") or "").strip()
        if not transition and row.get("metric_name") == "stability_class_transition" and isinstance(payload.get("transitions"), Mapping):
            for value in payload["transitions"].values():
                transitions[str(value)] += 1
            continue
        if transition:
            transitions[transition] += 1
            if transition == "INSUFFICIENT_DATA" or "INSUFFICIENT_DATA" in transition:
                insufficient += 1
        drift = str(payload.get("drift_class") or "").strip()
        if drift:
            trend_counts[drift] += 1
    return OrderedDict([
        ("transition_counts", OrderedDict(sorted(transitions.items()))),
        ("trend_counts", OrderedDict(sorted(trend_counts.items()))),
        ("insufficient_data_count", insufficient + sum(1 for row in rows if _stability_class(row) == "INSUFFICIENT_DATA")),
    ])


def _stability_trend(rows: Sequence[Mapping[str, Any]], metric_names: set[str]) -> OrderedDict[str, Any]:
    selected = [row for row in rows if str(row.get("metric_name")) in metric_names]
    drift_classes = [str(_payload(row).get("drift_class") or "") for row in selected]
    if "DETERIORATING" in drift_classes:
        trend = "DETERIORATING"
    elif "MIXED" in drift_classes:
        trend = "MIXED"
    elif "IMPROVING" in drift_classes and "STABLE" not in drift_classes:
        trend = "IMPROVING"
    elif "STABLE" in drift_classes:
        trend = "STABLE"
    else:
        values = [_metric_value(row) for row in selected]
        comparable = [value for value in values if value is not None]
        if len(comparable) < 2:
            trend = "INSUFFICIENT_DATA"
        else:
            trend_delta = _round(comparable[-1] - comparable[0])
            trend = "IMPROVING" if trend_delta and trend_delta > 0.02 else "DETERIORATING" if trend_delta and trend_delta < -0.02 else "STABLE"
    comparable = [value for value in (_metric_value(row) for row in selected) if value is not None]
    delta = _round(comparable[-1] - comparable[0]) if len(comparable) >= 2 else None
    return OrderedDict([("trend", trend), ("score_delta", delta), ("observations", len(selected))])


def build_observation_intelligence_report(*, client: Any | None = None, fact_rows: Iterable[Mapping[str, Any]] | None = None, report_path: str | Path | None = None, limit: int = DEFAULT_LIMIT) -> OrderedDict[str, Any]:
    rows = _rows(client=client, fact_rows=fact_rows, limit=limit)
    summary = get_observation_fact_summary(fact_rows=rows, limit=limit)
    transition_summary = get_stability_transition_summary(fact_rows=rows, limit=limit)
    intelligence = OrderedDict([
        ("schema_version", "obs_query1_v1"),
        ("source_table", OBSERVATION_FACTS_TABLE),
        ("source_behavior", OBSERVATION_FACTS_TABLE if client is not None else "bounded_local_fact_rows"),
        ("summary", summary),
        ("top_persistent_structures", get_top_persistent_structures(fact_rows=rows)),
        ("top_deteriorating_metrics", get_top_deteriorating_metrics(fact_rows=rows)),
        ("fragility_leaderboard", get_fragility_leaderboard(fact_rows=rows)),
        ("morphology_recurrence", get_morphology_recurrence(fact_rows=rows)),
        ("replay_stability_trend_summary", _stability_trend(rows, {"replay_stability_drift", "replay_density"})),
        ("contradiction_stability_trend_summary", _stability_trend(rows, {"contradiction_stability_drift", "contradiction_burden"})),
        ("concentration_stability_trend_summary", _stability_trend(rows, {"concentration_stability_drift", "sector_hhi", "subsector_hhi"})),
        ("stability_transition_summary", transition_summary),
        ("insufficient_data_counts", OrderedDict([("summary", summary["insufficient_data_count"]), ("transitions", transition_summary["insufficient_data_count"])])),
        ("governance_review", _governance_review()),
    ])
    report = render_observation_intelligence_markdown(intelligence)
    if report_path is not None:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
    intelligence["report"] = report
    return intelligence


def render_observation_intelligence_markdown(intelligence: Mapping[str, Any]) -> str:
    lines = [
        "# OBS-QUERY-1 Observation Fact Retrieval & Intelligence Layer\n",
        "## Source Behavior\n",
        f"- source_table: {intelligence.get('source_table')}\n",
        f"- source_behavior: {intelligence.get('source_behavior')}\n",
        "## Summary\n",
    ]
    summary = intelligence.get("summary") or {}
    lines.append(f"- rows: {summary.get('row_count')} snapshots: {summary.get('snapshot_count')} insufficient_data: {summary.get('insufficient_data_count')}\n")
    lines.append("## Top Persistent Structures\n")
    for item in intelligence.get("top_persistent_structures") or []:
        lines.append(f"- {item.get('structure')}: score={item.get('persistence_score')} class={item.get('stability_class')}\n")
    lines.append("## Top Deteriorating Metrics\n")
    for item in intelligence.get("top_deteriorating_metrics") or []:
        lines.append(f"- {item.get('metric_name')}: delta={item.get('score_delta')} class={item.get('drift_class')}\n")
    lines.append("## Fragility Leaderboard\n")
    for item in intelligence.get("fragility_leaderboard") or []:
        lines.append(f"- {item.get('entity_id')}: score={item.get('emerging_fragility_score')} class={item.get('emerging_fragility_class')}\n")
    lines.append("## Morphology Recurrence\n")
    for item in intelligence.get("morphology_recurrence") or []:
        lines.append(f"- {item.get('morphology')}: count={item.get('recurrence_count')} windows_or_snapshots={item.get('distinct_windows_or_snapshots')}\n")
    lines.append("## Stability Trend Summaries\n")
    for key in ("replay_stability_trend_summary", "contradiction_stability_trend_summary", "concentration_stability_trend_summary"):
        row = intelligence.get(key) or {}
        lines.append(f"- {key}: trend={row.get('trend')} delta={row.get('score_delta')} observations={row.get('observations')}\n")
    lines.append("## Stability-Class Transition Counts\n")
    for key, count in ((intelligence.get("stability_transition_summary") or {}).get("transition_counts") or {}).items():
        lines.append(f"- {key}: {count}\n")
    lines.append("## Insufficient-Data Counts\n")
    for key, count in (intelligence.get("insufficient_data_counts") or {}).items():
        lines.append(f"- {key}: {count}\n")
    lines.append("## Governance Review\n")
    for key, value in (intelligence.get("governance_review") or {}).items():
        lines.append(f"- {key}: {value}\n")
    return "".join(lines)
