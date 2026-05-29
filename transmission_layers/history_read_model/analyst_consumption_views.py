from __future__ import annotations

import json
from collections import OrderedDict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .historical_live_comparison import compare_historical_live_state
from .observation_fact_retrieval import HARD_LIMIT, OBSERVATION_FACTS_TABLE, bounded_limit
from .observation_intelligence_query import DEFAULT_LIMIT, retrieve_intelligence_question

SCHEMA_VERSION = "obs_query4_analyst_consumption_view_v1"
VIEW_TYPES = (
    "ecosystem_briefing",
    "change_monitor",
    "persistence_monitor",
    "anomaly_monitor",
    "investigation_queue",
)
GENERATION_TIMESTAMP = "deterministic_retrieval_only"

_VIEW_BLUEPRINTS: Mapping[str, Sequence[tuple[str, str, str]]] = {
    "ecosystem_briefing": (
        ("Persistent Structures", "query", "persisted"),
        ("Dominant Structures", "query", "dominant"),
        ("Recurring Structures", "query", "recurred"),
        ("Historical-Live Overlap", "comparison", "baseline_overlap"),
        ("Significant Deviations", "comparison", "baseline_deviation"),
        ("Investigation Candidates", "queue", "investigation_queue"),
    ),
    "change_monitor": (
        ("Changed Structures", "query", "changed"),
        ("Transitioning Structures", "query", "transitioned"),
        ("Weakening Structures", "query", "weakened"),
        ("Historical-Live Deviations", "comparison", "baseline_deviation"),
        ("Persistent Structures Weakening Live", "comparison", "persistent_weakening_live"),
        ("Historically Weak Structures Strengthening Live", "comparison", "weak_strengthening_live"),
    ),
    "persistence_monitor": (
        ("Persistent Structures", "query", "persisted"),
        ("Recurring Structures", "query", "recurred"),
        ("Dominant Structures", "query", "dominant"),
        ("Historical-Live Recurrence", "comparison", "historical_recurrence"),
        ("Persistent Structures Weakening Live", "comparison", "persistent_weakening_live"),
    ),
    "anomaly_monitor": (
        ("Live-Only Anomalies", "comparison", "live_anomalies"),
        ("Historical-Live Deviations", "comparison", "baseline_deviation"),
        ("Changed Structures", "query", "changed"),
        ("Weakening Structures", "query", "weakened"),
    ),
    "investigation_queue": (
        ("Investigation Queue", "queue", "investigation_queue"),
        ("Changed Structure Context", "query", "changed"),
        ("Weakening Structure Context", "query", "weakened"),
    ),
}

_QUEUE_SOURCES: Sequence[tuple[str, str, str]] = (
    ("Live-Only Anomalies", "live_anomalies", "live_only_anomaly"),
    ("Strong Historical-Live Deviations", "baseline_deviation", "historical_live_deviation"),
    ("Persistent Structures Weakening Live", "persistent_weakening_live", "persistent_weakening_live"),
    ("Historically Weak Structures Strengthening Live", "weak_strengthening_live", "historically_weak_strengthening_live"),
)
_QUEUE_SOURCE_ORDER = {source: index for index, (_label, _comparison_type, source) in enumerate(_QUEUE_SOURCES)}


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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


def _parameters(*, view_type: str, symbol: str | None, taxonomy: str | None, snapshot_date: str | None, limit: int | None) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("view_type", view_type),
        ("symbol", symbol),
        ("taxonomy", taxonomy),
        ("snapshot_date", snapshot_date),
        ("limit", limit),
    ])


def _governance_certification() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "OBS-QUERY-4"),
        ("retrieval_only", True),
        ("consumption_only", True),
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
        ("generation_timestamp_policy", "fixed deterministic sentinel; no wall-clock timestamp used"),
    ])


def _metric_sort_value(item: Mapping[str, Any]) -> float:
    metric = item.get("ranking_metric") or {}
    value = metric.get("value") if isinstance(metric, Mapping) else None
    try:
        return abs(float(value)) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _comparison_fact_ids(item: Mapping[str, Any]) -> list[str]:
    return sorted({str(fact_id) for fact_id in [*(item.get("historical_supporting_fact_ids") or []), *(item.get("live_supporting_fact_ids") or [])] if str(fact_id)})


def _view_item_from_query(item: Mapping[str, Any], *, query_type: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("source_type", "OBS-QUERY-2"),
        ("source_query_type", query_type),
        ("identifier", item.get("identifier")),
        ("ranking_metric", item.get("ranking_metric") or OrderedDict()),
        ("classification", None),
        ("delta", None),
        ("supporting_fact_ids", list(item.get("supporting_fact_ids") or [])),
        ("supporting_evidence_ids", list(item.get("supporting_evidence_ids") or [])),
        ("supporting_evidence", list(item.get("supporting_evidence") or [])),
        ("source_phases", list(item.get("source_phases") or [])),
    ])


def _view_item_from_comparison(item: Mapping[str, Any], *, comparison_type: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("source_type", "OBS-QUERY-3"),
        ("source_comparison_type", comparison_type),
        ("identifier", item.get("identifier")),
        ("classification", item.get("classification")),
        ("ranking_metric", item.get("ranking_metric") or OrderedDict()),
        ("historical_metric", item.get("historical_metric") or OrderedDict()),
        ("live_metric", item.get("live_metric") or OrderedDict()),
        ("delta", item.get("delta")),
        ("supporting_fact_ids", _comparison_fact_ids(item)),
        ("historical_supporting_fact_ids", list(item.get("historical_supporting_fact_ids") or [])),
        ("live_supporting_fact_ids", list(item.get("live_supporting_fact_ids") or [])),
        ("supporting_evidence_ids", list(item.get("supporting_evidence_ids") or [])),
        ("source_phases", list(item.get("source_phases") or [])),
    ])


def _queue_item(item: Mapping[str, Any], *, comparison_type: str, queue_source: str) -> OrderedDict[str, Any]:
    base = _view_item_from_comparison(item, comparison_type=comparison_type)
    base["queue_source"] = queue_source
    return base


def _sort_items(items: Sequence[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    return [OrderedDict(item) for item in sorted(items, key=lambda item: (-_metric_sort_value(item), str(item.get("classification") or ""), str(item.get("identifier") or ""), str(item.get("source_query_type") or item.get("source_comparison_type") or "")))]


def _sort_queue_items(items: Sequence[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    return [OrderedDict(item) for item in sorted(items, key=lambda item: (_QUEUE_SOURCE_ORDER.get(str(item.get("queue_source")), 99), -_metric_sort_value(item), str(item.get("classification") or ""), str(item.get("identifier") or "")))]


def _section(section_name: str, items: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    fact_ids = sorted({str(fact_id) for item in items for fact_id in (item.get("supporting_fact_ids") or []) if str(fact_id)})
    evidence_ids = sorted({str(evidence_id) for item in items for evidence_id in (item.get("supporting_evidence_ids") or []) if str(evidence_id)})
    supporting_evidence: list[Mapping[str, Any]] = []
    seen_evidence_rows: set[tuple[str, str]] = set()
    for item in items:
        for evidence in item.get("supporting_evidence") or []:
            if not isinstance(evidence, Mapping):
                continue
            key = (str(evidence.get("fact_id") or ""), str(evidence.get("evidence_id") or ""))
            if key in seen_evidence_rows:
                continue
            seen_evidence_rows.add(key)
            supporting_evidence.append(evidence)
    return OrderedDict([
        ("section_name", section_name),
        ("item_count", len(items)),
        ("items", list(items)),
        ("supporting_facts", fact_ids),
        ("supporting_evidence", evidence_ids),
        ("supporting_evidence_rows", supporting_evidence),
    ])


def _query_result(cache: dict[str, Mapping[str, Any]], query_type: str, *, client: Any | None, fact_rows: Iterable[Mapping[str, Any]] | None, symbol: str | None, taxonomy: str | None, snapshot_date: str | None, limit: int) -> Mapping[str, Any]:
    if query_type not in cache:
        cache[query_type] = retrieve_intelligence_question(query_type=query_type, client=client, fact_rows=fact_rows, symbol=symbol, taxonomy=taxonomy, snapshot_date=snapshot_date, limit=limit)
    return cache[query_type]


def _comparison_result(cache: dict[str, Mapping[str, Any]], comparison_type: str, *, client: Any | None, fact_rows: Iterable[Mapping[str, Any]] | None, symbol: str | None, taxonomy: str | None, snapshot_date: str | None, limit: int) -> Mapping[str, Any]:
    if comparison_type not in cache:
        cache[comparison_type] = compare_historical_live_state(comparison_type=comparison_type, client=client, fact_rows=fact_rows, symbol=symbol, taxonomy=taxonomy, snapshot_date=snapshot_date, limit=limit)
    return cache[comparison_type]


def _build_queue(*, comparison_cache: dict[str, Mapping[str, Any]], client: Any | None, fact_rows: Iterable[Mapping[str, Any]] | None, symbol: str | None, taxonomy: str | None, snapshot_date: str | None, limit: int) -> list[OrderedDict[str, Any]]:
    items: list[Mapping[str, Any]] = []
    for _label, comparison_type, queue_source in _QUEUE_SOURCES:
        result = _comparison_result(comparison_cache, comparison_type, client=client, fact_rows=fact_rows, symbol=symbol, taxonomy=taxonomy, snapshot_date=snapshot_date, limit=limit)
        items.extend(_queue_item(item, comparison_type=comparison_type, queue_source=queue_source) for item in result.get("results") or [])
    return _sort_queue_items(items)[:limit]


def build_consumption_view(
    *,
    view_type: str,
    client: Any | None = None,
    fact_rows: Iterable[Mapping[str, Any]] | None = None,
    symbol: str | None = None,
    taxonomy: str | None = None,
    snapshot_date: str | date | datetime | None = None,
    limit: int | None = DEFAULT_LIMIT,
) -> OrderedDict[str, Any]:
    normalized_view_type = str(view_type).strip().lower()
    if normalized_view_type not in VIEW_TYPES:
        raise ValueError(f"view_type must be one of: {', '.join(VIEW_TYPES)}")
    safe_limit = bounded_limit(limit if limit is not None else DEFAULT_LIMIT)
    normalized_symbol = _clean(symbol).upper() if _clean(symbol) else None
    normalized_taxonomy = _clean(taxonomy)
    normalized_snapshot_date = _normalize_date(snapshot_date)

    query_cache: dict[str, Mapping[str, Any]] = {}
    comparison_cache: dict[str, Mapping[str, Any]] = {}
    sections: list[OrderedDict[str, Any]] = []

    for section_name, source_kind, source_name in _VIEW_BLUEPRINTS[normalized_view_type]:
        if source_kind == "query":
            result = _query_result(query_cache, source_name, client=client, fact_rows=fact_rows, symbol=normalized_symbol, taxonomy=normalized_taxonomy, snapshot_date=normalized_snapshot_date, limit=safe_limit)
            items = _sort_items(_view_item_from_query(item, query_type=source_name) for item in result.get("results") or [])[:safe_limit]
        elif source_kind == "comparison":
            result = _comparison_result(comparison_cache, source_name, client=client, fact_rows=fact_rows, symbol=normalized_symbol, taxonomy=normalized_taxonomy, snapshot_date=normalized_snapshot_date, limit=safe_limit)
            items = _sort_items(_view_item_from_comparison(item, comparison_type=source_name) for item in result.get("results") or [])[:safe_limit]
        else:
            items = _build_queue(comparison_cache=comparison_cache, client=client, fact_rows=fact_rows, symbol=normalized_symbol, taxonomy=normalized_taxonomy, snapshot_date=normalized_snapshot_date, limit=safe_limit)
        sections.append(_section(section_name, items))

    supporting_fact_ids = sorted({fact_id for section in sections for fact_id in section.get("supporting_facts", [])})
    supporting_evidence_ids = sorted({evidence_id for section in sections for evidence_id in section.get("supporting_evidence", [])})
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("source_table", OBSERVATION_FACTS_TABLE),
        ("view_type", normalized_view_type),
        ("generation_timestamp", GENERATION_TIMESTAMP),
        ("query_parameters", _parameters(view_type=normalized_view_type, symbol=normalized_symbol, taxonomy=normalized_taxonomy, snapshot_date=normalized_snapshot_date, limit=limit)),
        ("hard_limit", HARD_LIMIT),
        ("effective_limit", safe_limit),
        ("source_query_types", sorted(query_cache)),
        ("source_comparison_types", sorted(comparison_cache)),
        ("sections", sections),
        ("supporting_fact_ids", supporting_fact_ids),
        ("supporting_evidence_ids", supporting_evidence_ids),
        ("governance_certification", _governance_certification()),
    ])


def build_ecosystem_briefing_view(**kwargs: Any) -> OrderedDict[str, Any]:
    return build_consumption_view(view_type="ecosystem_briefing", **kwargs)


def build_change_monitor_view(**kwargs: Any) -> OrderedDict[str, Any]:
    return build_consumption_view(view_type="change_monitor", **kwargs)


def build_persistence_monitor_view(**kwargs: Any) -> OrderedDict[str, Any]:
    return build_consumption_view(view_type="persistence_monitor", **kwargs)


def build_anomaly_monitor_view(**kwargs: Any) -> OrderedDict[str, Any]:
    return build_consumption_view(view_type="anomaly_monitor", **kwargs)


def build_investigation_queue_view(**kwargs: Any) -> OrderedDict[str, Any]:
    return build_consumption_view(view_type="investigation_queue", **kwargs)


def render_consumption_view_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        f"# OBS-QUERY-4 Analyst Consumption View: {result.get('view_type')}\n\n",
        "# View Summary\n",
        f"- schema_version: {result.get('schema_version')}\n",
        f"- view_type: {result.get('view_type')}\n",
        f"- generation_timestamp: {result.get('generation_timestamp')}\n",
        f"- effective_limit: {result.get('effective_limit')}\n",
        f"- source_query_types: {', '.join(result.get('source_query_types') or []) or 'none'}\n",
        f"- source_comparison_types: {', '.join(result.get('source_comparison_types') or []) or 'none'}\n\n",
    ]
    for section in result.get("sections") or []:
        lines.append(f"## {section.get('section_name')}\n")
        lines.append(f"- item_count: {section.get('item_count')}\n\n")
        lines.append("| identifier | source | classification | ranking_metric | delta | supporting_facts | supporting_evidence |\n")
        lines.append("| --- | --- | --- | ---: | ---: | --- | --- |\n")
        for item in section.get("items") or []:
            metric = item.get("ranking_metric") or {}
            source = item.get("source_query_type") or item.get("source_comparison_type") or item.get("queue_source") or ""
            lines.append(
                f"| {item.get('identifier') or ''} | {source} | {item.get('classification') or ''} | {metric.get('name')}={metric.get('value')} | {item.get('delta') if item.get('delta') is not None else ''} | {', '.join(item.get('supporting_fact_ids') or [])} | {', '.join(item.get('supporting_evidence_ids') or [])} |\n"
            )
        if not section.get("items"):
            lines.append("| none |  |  |  |  |  |  |\n")
        lines.append("\n")

    lines.append("## Supporting Facts\n")
    for fact_id in result.get("supporting_fact_ids") or []:
        lines.append(f"- {fact_id}\n")
    if not result.get("supporting_fact_ids"):
        lines.append("- none\n")

    lines.append("\n## Supporting Evidence\n")
    for evidence_id in result.get("supporting_evidence_ids") or []:
        lines.append(f"- {evidence_id}\n")
    if not result.get("supporting_evidence_ids"):
        lines.append("- none\n")

    lines.append("\n## Governance Certification\n")
    for key, value in (result.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {value}\n")
    return "".join(lines)


def write_consumption_view_outputs(result: Mapping[str, Any], *, output_json: str | Path | None = None, output_md: str | Path | None = None) -> OrderedDict[str, str | None]:
    json_path = Path(output_json) if output_json else None
    md_path = Path(output_md) if output_md else None
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_consumption_view_markdown(result), encoding="utf-8")
    return OrderedDict([("output_json", str(json_path) if json_path else None), ("output_md", str(md_path) if md_path else None)])
