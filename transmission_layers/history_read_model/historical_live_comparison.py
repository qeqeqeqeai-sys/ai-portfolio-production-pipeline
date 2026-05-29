from __future__ import annotations

import json
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .observation_fact_retrieval import HARD_LIMIT, OBSERVATION_FACTS_TABLE, READ_COLUMNS, bounded_limit
from .observation_intelligence_query import MAX_SCAN_ROWS

DEFAULT_LIMIT = 25
COMPARISON_TYPES = (
    "baseline_overlap",
    "live_anomalies",
    "historical_recurrence",
    "persistent_weakening_live",
    "weak_strengthening_live",
    "baseline_deviation",
)
CLASSIFICATIONS = (
    "historical_and_live",
    "live_only",
    "historical_only",
    "live_weaker_than_historical",
    "live_stronger_than_historical",
    "live_deviates_from_historical",
    "recurring_historical_pattern",
)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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


def _date_prefix(value: Any) -> str:
    return str(value or "")[:10]


def _normalize_date(value: str | date | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    return datetime.strptime(text[:10], "%Y-%m-%d").date().isoformat()


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb")
    return payload if isinstance(payload, Mapping) else {}


def _fact_id(row: Mapping[str, Any]) -> str:
    for key in ("id", "fact_id", "duplicate_prevention_key"):
        value = _clean(row.get(key))
        if value:
            return value
    payload = _payload(row)
    return _clean(payload.get("fact_id") or payload.get("evidence_id")) or ""


def _evidence_id(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    return _clean(payload.get("evidence_id") or payload.get("source_evidence_id") or row.get("evidence_id") or row.get("id") or row.get("duplicate_prevention_key")) or ""


def _time_key(row: Mapping[str, Any]) -> str:
    return str(row.get("loaded_at") or row.get("created_at") or row.get("completed_at") or row.get("run_id") or "")


def _stable_row_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (_time_key(row), str(row.get("run_id") or ""), str(row.get("phase_id") or ""), str(row.get("entity_type") or ""), str(row.get("entity_id") or ""), _fact_id(row))


def _row_symbol(row: Mapping[str, Any]) -> str | None:
    payload = _payload(row)
    for value in (row.get("symbol"), payload.get("symbol"), payload.get("ticker")):
        cleaned = _clean(value)
        if cleaned:
            return cleaned.upper()
    if str(row.get("entity_type") or "").lower() == "symbol":
        cleaned = _clean(row.get("entity_id"))
        if cleaned:
            return cleaned.upper()
    return None


def _identifier(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    for key in ("identifier", "dimension", "structure", "morphology", "stability_dimension", "taxonomy"):
        value = _clean(payload.get(key))
        if value:
            return value
    entity_id = _clean(row.get("entity_id"))
    if entity_id:
        return entity_id.rsplit(":", 1)[-1] if ":" in entity_id else entity_id
    return _clean(row.get("metric_name")) or "unknown"


def _metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = _payload(row)
    for key in ("persistence_score", "dominance_score", "concentration_score", "recurrence_score", "weakening_score", "score", "value", "delta", "change", "score_delta"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _source_phase(row: Mapping[str, Any]) -> str | None:
    return _clean(row.get("phase_id") or _payload(row).get("source_phase"))


def _is_historical(row: Mapping[str, Any], historical_source_layer: str | None) -> bool:
    phase = str(_source_phase(row) or "").upper()
    if historical_source_layer:
        return phase == historical_source_layer.upper()
    return phase.startswith("HIST") or phase.startswith("OPS-HIST")


def _is_live(row: Mapping[str, Any], live_source_layer: str | None) -> bool:
    phase = str(_source_phase(row) or "").upper()
    if live_source_layer:
        return phase == live_source_layer.upper()
    return phase.startswith("LIVE") or phase.startswith("OPS-LIVE")


def _execute(query: Any) -> list[Mapping[str, Any]]:
    result = query.execute()
    data = getattr(result, "data", result)
    return [row for row in (data or []) if isinstance(row, Mapping)]


def _query_rows(client: Any, *, taxonomy: str | None, symbol: str | None, snapshot_date: str | None, scan_limit: int) -> list[Mapping[str, Any]]:
    query = client.table(OBSERVATION_FACTS_TABLE).select(READ_COLUMNS)
    if taxonomy:
        query = query.eq("metric_name", taxonomy)
    if symbol:
        query = query.eq("entity_type", "symbol").eq("entity_id", symbol)
    if snapshot_date and hasattr(query, "gte") and hasattr(query, "lt"):
        start = f"{snapshot_date}T00:00:00Z"
        end = f"{(datetime.strptime(snapshot_date, '%Y-%m-%d').date() + timedelta(days=1)).isoformat()}T00:00:00Z"
        query = query.gte("loaded_at", start).lt("loaded_at", end)
    query = query.order("loaded_at", desc=False).order("run_id", desc=False).order("id", desc=False).limit(scan_limit)
    return _execute(query)


def _load_rows(
    *,
    client: Any | None,
    fact_rows: Iterable[Mapping[str, Any]] | None,
    symbol: str | None,
    taxonomy: str | None,
    historical_source_layer: str | None,
    live_source_layer: str | None,
    snapshot_date: str | None,
    scan_limit: int,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    rows = _query_rows(client, taxonomy=taxonomy, symbol=symbol, snapshot_date=snapshot_date, scan_limit=scan_limit) if client is not None else [row for row in (fact_rows or []) if isinstance(row, Mapping)]
    historical_rows: list[Mapping[str, Any]] = []
    live_rows: list[Mapping[str, Any]] = []
    for row in rows:
        if snapshot_date and _date_prefix(row.get("loaded_at") or row.get("created_at")) != snapshot_date:
            continue
        if symbol and _row_symbol(row) != symbol:
            continue
        if taxonomy and row.get("metric_name") != taxonomy:
            continue
        if _is_historical(row, historical_source_layer):
            historical_rows.append(row)
        if _is_live(row, live_source_layer):
            live_rows.append(row)
    return sorted(historical_rows, key=_stable_row_key)[:scan_limit], sorted(live_rows, key=_stable_row_key)[:scan_limit]


def _metric_summary(rows: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    values = [_metric_value(row) for row in rows]
    numeric_values = sorted({_round(value) for value in values if value is not None})
    representative = max(numeric_values) if numeric_values else None
    return OrderedDict([
        ("fact_count", len({_fact_id(row) for row in rows if _fact_id(row)})),
        ("numeric_values", numeric_values),
        ("representative_value", representative),
    ])


def _supporting_evidence(row: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("fact_id", _fact_id(row)),
        ("evidence_id", _evidence_id(row)),
        ("artifact_id", row.get("artifact_id")),
        ("run_id", row.get("run_id")),
        ("source_phase", _source_phase(row)),
    ])


def _group_by_identifier(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_identifier(row)].append(row)
    return {key: sorted(value, key=_stable_row_key) for key, value in grouped.items()}


def _ranking_metric(comparison_type: str, historical_rows: Sequence[Mapping[str, Any]], live_rows: Sequence[Mapping[str, Any]], delta: float | None) -> OrderedDict[str, Any]:
    if comparison_type in {"persistent_weakening_live", "weak_strengthening_live", "baseline_deviation"}:
        return OrderedDict([("name", "absolute_numeric_delta"), ("value", _round(abs(delta)) if delta is not None else None)])
    if comparison_type == "historical_recurrence":
        return OrderedDict([("name", "historical_live_recurrence_count"), ("value", len(historical_rows) + len(live_rows))])
    if comparison_type == "live_anomalies":
        return OrderedDict([("name", "live_fact_count"), ("value", len(live_rows))])
    return OrderedDict([("name", "comparison_fact_count"), ("value", len(historical_rows) + len(live_rows))])


def _classification(comparison_type: str, has_historical: bool, has_live: bool, delta: float | None) -> str | None:
    if comparison_type == "baseline_overlap":
        if has_historical and has_live:
            return "historical_and_live"
        if has_live:
            return "live_only"
        if has_historical:
            return "historical_only"
    if comparison_type == "live_anomalies" and has_live and not has_historical:
        return "live_only"
    if comparison_type == "historical_recurrence" and has_historical and has_live:
        return "recurring_historical_pattern"
    if comparison_type == "persistent_weakening_live" and has_historical and has_live and delta is not None and delta < 0:
        return "live_weaker_than_historical"
    if comparison_type == "weak_strengthening_live" and has_historical and has_live and delta is not None and delta > 0:
        return "live_stronger_than_historical"
    if comparison_type == "baseline_deviation" and has_historical and has_live and delta is not None and delta != 0:
        return "live_deviates_from_historical"
    return None


def _build_results(comparison_type: str, historical_rows: Sequence[Mapping[str, Any]], live_rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[OrderedDict[str, Any]]:
    historical = _group_by_identifier(historical_rows)
    live = _group_by_identifier(live_rows)
    results: list[OrderedDict[str, Any]] = []
    for identifier in sorted(set(historical) | set(live)):
        h_rows = historical.get(identifier, [])
        l_rows = live.get(identifier, [])
        historical_metric = _metric_summary(h_rows)
        live_metric = _metric_summary(l_rows)
        h_value = historical_metric.get("representative_value")
        l_value = live_metric.get("representative_value")
        delta = _round(float(l_value) - float(h_value)) if h_value is not None and l_value is not None else None
        classification = _classification(comparison_type, bool(h_rows), bool(l_rows), delta)
        if classification is None:
            continue
        h_fact_ids = sorted({_fact_id(row) for row in h_rows if _fact_id(row)})
        l_fact_ids = sorted({_fact_id(row) for row in l_rows if _fact_id(row)})
        evidence_ids = sorted({_evidence_id(row) for row in [*h_rows, *l_rows] if _evidence_id(row)})
        results.append(OrderedDict([
            ("identifier", identifier),
            ("classification", classification),
            ("historical_metric", historical_metric),
            ("live_metric", live_metric),
            ("delta", delta),
            ("ranking_metric", _ranking_metric(comparison_type, h_rows, l_rows, delta)),
            ("historical_supporting_fact_ids", h_fact_ids),
            ("live_supporting_fact_ids", l_fact_ids),
            ("supporting_evidence_ids", evidence_ids),
            ("source_phases", sorted({_source_phase(row) for row in [*h_rows, *l_rows] if _source_phase(row)})),
        ]))
    return sorted(results, key=lambda item: (-(float(item["ranking_metric"].get("value") or 0)), str(item["classification"]), str(item["identifier"])))[:limit]


def _governance_certification() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "OBS-QUERY-3"),
        ("retrieval_only", True),
        ("db2_facts_only", True),
        ("no_synthesis", True),
        ("no_new_intelligence_generation", True),
        ("no_fact_creation", True),
        ("provider_api_calls_enabled", False),
        ("db_writes_enabled", False),
        ("schema_migrations_enabled", False),
        ("predictions_enabled", False),
        ("recommendations_enabled", False),
        ("market_actions_enabled", False),
        ("source_of_truth", OBSERVATION_FACTS_TABLE),
    ])


def _parameters(*, comparison_type: str, historical_source_layer: str | None, live_source_layer: str | None, symbol: str | None, taxonomy: str | None, snapshot_date: str | None, limit: int | None) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("comparison_type", comparison_type),
        ("historical_source_layer", historical_source_layer),
        ("live_source_layer", live_source_layer),
        ("symbol", symbol),
        ("taxonomy", taxonomy),
        ("snapshot_date", snapshot_date),
        ("limit", limit),
    ])


def compare_historical_live_state(
    *,
    comparison_type: str = "baseline_overlap",
    client: Any | None = None,
    fact_rows: Iterable[Mapping[str, Any]] | None = None,
    historical_source_layer: str | None = None,
    live_source_layer: str | None = None,
    symbol: str | None = None,
    taxonomy: str | None = None,
    snapshot_date: str | date | datetime | None = None,
    limit: int | None = DEFAULT_LIMIT,
) -> OrderedDict[str, Any]:
    normalized_comparison_type = str(comparison_type).strip().lower()
    if normalized_comparison_type not in COMPARISON_TYPES:
        raise ValueError(f"comparison_type must be one of: {', '.join(COMPARISON_TYPES)}")
    safe_limit = bounded_limit(limit if limit is not None else DEFAULT_LIMIT)
    normalized_historical_layer = _clean(historical_source_layer)
    normalized_live_layer = _clean(live_source_layer)
    normalized_symbol = _clean(symbol).upper() if _clean(symbol) else None
    normalized_taxonomy = _clean(taxonomy)
    normalized_snapshot_date = _normalize_date(snapshot_date)
    historical_rows, live_rows = _load_rows(
        client=client,
        fact_rows=fact_rows,
        symbol=normalized_symbol,
        taxonomy=normalized_taxonomy,
        historical_source_layer=normalized_historical_layer,
        live_source_layer=normalized_live_layer,
        snapshot_date=normalized_snapshot_date,
        scan_limit=MAX_SCAN_ROWS,
    )
    results = _build_results(normalized_comparison_type, historical_rows, live_rows, limit=safe_limit)
    historical_fact_ids = sorted({fact_id for item in results for fact_id in (item.get("historical_supporting_fact_ids") or [])})
    live_fact_ids = sorted({fact_id for item in results for fact_id in (item.get("live_supporting_fact_ids") or [])})
    evidence_ids = sorted({evidence_id for item in results for evidence_id in (item.get("supporting_evidence_ids") or [])})
    supporting_evidence = [_supporting_evidence(row) for row in [*historical_rows, *live_rows] if _evidence_id(row) in set(evidence_ids)]
    return OrderedDict([
        ("schema_version", "obs_query3_historical_live_comparison_v1"),
        ("source_table", OBSERVATION_FACTS_TABLE),
        ("query_type", "historical_live_comparison"),
        ("comparison_type", normalized_comparison_type),
        ("query_parameters", _parameters(comparison_type=normalized_comparison_type, historical_source_layer=normalized_historical_layer, live_source_layer=normalized_live_layer, symbol=normalized_symbol, taxonomy=normalized_taxonomy, snapshot_date=normalized_snapshot_date, limit=limit)),
        ("result_count", len(results)),
        ("hard_limit", HARD_LIMIT),
        ("effective_limit", safe_limit),
        ("results", results),
        ("historical_fact_ids", historical_fact_ids),
        ("live_fact_ids", live_fact_ids),
        ("supporting_evidence_ids", evidence_ids),
        ("supporting_evidence", supporting_evidence),
        ("governance_certification", _governance_certification()),
    ])


def get_live_recurring_historical_patterns(**kwargs: Any) -> OrderedDict[str, Any]:
    return compare_historical_live_state(comparison_type="historical_recurrence", **kwargs)


def get_live_anomalies_vs_historical(**kwargs: Any) -> OrderedDict[str, Any]:
    return compare_historical_live_state(comparison_type="live_anomalies", **kwargs)


def get_persistent_structures_weakening_live(**kwargs: Any) -> OrderedDict[str, Any]:
    return compare_historical_live_state(comparison_type="persistent_weakening_live", **kwargs)


def get_historically_weak_structures_strengthening_live(**kwargs: Any) -> OrderedDict[str, Any]:
    return compare_historical_live_state(comparison_type="weak_strengthening_live", **kwargs)


def get_live_baseline_deviations(**kwargs: Any) -> OrderedDict[str, Any]:
    return compare_historical_live_state(comparison_type="baseline_deviation", **kwargs)


def render_historical_live_comparison_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# OBS-QUERY-3 Historical vs Live Intelligence Comparison\n\n",
        "## Query summary\n",
        f"- query_type: {result.get('query_type')}\n",
        f"- comparison_type: {result.get('comparison_type')}\n",
        f"- source_table: {result.get('source_table')}\n",
        f"- result_count: {result.get('result_count')}\n",
        f"- effective_limit: {result.get('effective_limit')}\n",
        f"- hard_limit: {result.get('hard_limit')}\n\n",
        "## Comparison results table\n",
        "| identifier | classification | historical_value | live_value | delta | ranking_metric | historical_facts | live_facts | source_phases |\n",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |\n",
    ]
    for item in result.get("results") or []:
        h_metric = item.get("historical_metric") or {}
        l_metric = item.get("live_metric") or {}
        metric = item.get("ranking_metric") or {}
        lines.append(
            f"| {item.get('identifier') or ''} | {item.get('classification') or ''} | {h_metric.get('representative_value') if h_metric.get('representative_value') is not None else ''} | {l_metric.get('representative_value') if l_metric.get('representative_value') is not None else ''} | {item.get('delta') if item.get('delta') is not None else ''} | {metric.get('name')}={metric.get('value')} | {', '.join(item.get('historical_supporting_fact_ids') or [])} | {', '.join(item.get('live_supporting_fact_ids') or [])} | {', '.join(item.get('source_phases') or [])} |\n"
        )
    if not result.get("results"):
        lines.append("| none |  |  |  |  |  |  |  |  |\n")

    lines.append("\n## Historical supporting facts\n")
    for fact_id in result.get("historical_fact_ids") or []:
        lines.append(f"- {fact_id}\n")
    if not result.get("historical_fact_ids"):
        lines.append("- none\n")

    lines.append("\n## Live supporting facts\n")
    for fact_id in result.get("live_fact_ids") or []:
        lines.append(f"- {fact_id}\n")
    if not result.get("live_fact_ids"):
        lines.append("- none\n")

    lines.append("\n## Supporting evidence\n")
    for evidence_id in result.get("supporting_evidence_ids") or []:
        lines.append(f"- {evidence_id}\n")
    if not result.get("supporting_evidence_ids"):
        lines.append("- none\n")

    lines.append("\n## Governance certification\n")
    for key, value in (result.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {value}\n")
    return "".join(lines)


def write_historical_live_comparison_outputs(result: Mapping[str, Any], *, output_json: str | Path | None = None, output_md: str | Path | None = None) -> OrderedDict[str, str | None]:
    json_path = Path(output_json) if output_json else None
    md_path = Path(output_md) if output_md else None
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_historical_live_comparison_markdown(result), encoding="utf-8")
    return OrderedDict([("output_json", str(json_path) if json_path else None), ("output_md", str(md_path) if md_path else None)])
