from __future__ import annotations

import json
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .observation_fact_retrieval import HARD_LIMIT, OBSERVATION_FACTS_TABLE, READ_COLUMNS, bounded_limit

DEFAULT_LIMIT = 25
MAX_SCAN_ROWS = 1000
QUERY_TYPES = ("persisted", "changed", "recurred", "dominant", "weakened", "transitioned")

_DRIFT_SEVERITY = {"DETERIORATING": 4, "WEAKENING": 4, "WEAKENED": 4, "MIXED": 3, "CHANGED": 2, "STABLE": 1, "IMPROVING": 0, "INSUFFICIENT_DATA": -1}


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


def _dimension(row: Mapping[str, Any]) -> str:
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
    for key in ("persistence_score", "dominance_score", "concentration_score", "recurrence_score", "score", "value", "delta", "change", "score_delta"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _source_phase(row: Mapping[str, Any]) -> str | None:
    return _clean(row.get("phase_id") or _payload(row).get("source_phase"))


def _supporting_evidence(row: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("fact_id", _fact_id(row)),
        ("evidence_id", _evidence_id(row)),
        ("artifact_id", row.get("artifact_id")),
        ("run_id", row.get("run_id")),
        ("source_phase", _source_phase(row)),
    ])


def _execute(query: Any) -> list[Mapping[str, Any]]:
    result = query.execute()
    data = getattr(result, "data", result)
    return [row for row in (data or []) if isinstance(row, Mapping)]


def _query_rows(
    client: Any,
    *,
    symbol: str | None,
    taxonomy: str | None,
    source_layer: str | None,
    snapshot_date: str | None,
    scan_limit: int,
) -> list[Mapping[str, Any]]:
    query = client.table(OBSERVATION_FACTS_TABLE).select(READ_COLUMNS)
    if source_layer:
        query = query.eq("phase_id", source_layer)
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
    source_layer: str | None,
    snapshot_date: str | None,
    scan_limit: int,
) -> list[Mapping[str, Any]]:
    if client is not None:
        rows = _query_rows(client, symbol=symbol, taxonomy=taxonomy, source_layer=source_layer, snapshot_date=snapshot_date, scan_limit=scan_limit)
    else:
        rows = [row for row in (fact_rows or []) if isinstance(row, Mapping)]
    selected = []
    for row in rows:
        if snapshot_date and _date_prefix(row.get("loaded_at") or row.get("created_at")) != snapshot_date:
            continue
        if symbol and _row_symbol(row) != symbol:
            continue
        if taxonomy and row.get("metric_name") != taxonomy:
            continue
        if source_layer and row.get("phase_id") != source_layer:
            continue
        selected.append(row)
    return sorted(selected, key=_stable_row_key)[:scan_limit]


def _contains_any(text: str, needles: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def _persistence_score(row: Mapping[str, Any]) -> float | None:
    payload = _payload(row)
    for key in ("persistence_score", "overall_persistence_score"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    if str(row.get("metric_name") or "") in {"persistence_score", "overall_persistence_score"} or _contains_any(str(row.get("metric_name") or ""), ("persistence", "persisted")):
        return _metric_value(row)
    if str(payload.get("stability_class") or "").upper() == "STABLE":
        return _metric_value(row) or 1.0
    return None


def _change_score(row: Mapping[str, Any]) -> float | None:
    payload = _payload(row)
    drift = str(payload.get("drift_class") or row.get("drift_class") or "").upper()
    transition = _clean(payload.get("stability_class_transition"))
    metric = str(row.get("metric_name") or "")
    explicit = None
    for key in ("change_score", "delta", "score_delta", "change", "drift_delta"):
        explicit = _number(payload.get(key))
        if explicit is not None:
            break
    value = explicit if explicit is not None else _metric_value(row)
    if transition and "->" in transition:
        return 100.0 + (abs(value) if value is not None else 1.0)
    if drift and drift not in {"STABLE", "INSUFFICIENT_DATA"}:
        return float(_DRIFT_SEVERITY.get(drift, 1)) + (abs(value) if value is not None else 0.0)
    if _contains_any(metric, ("drift", "delta", "change", "transition")) and value is not None and value != 0:
        return abs(value)
    return None


def _dominance_score(row: Mapping[str, Any]) -> float | None:
    payload = _payload(row)
    for key in ("dominance_score", "concentration_score", "hhi", "share", "weight"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    metric = str(row.get("metric_name") or "")
    if _contains_any(metric, ("dominance", "dominant", "concentration", "hhi", "share", "weight")):
        return _metric_value(row)
    return None


def _weakening_score(row: Mapping[str, Any]) -> float | None:
    payload = _payload(row)
    drift = str(payload.get("drift_class") or row.get("drift_class") or "").upper()
    metric = str(row.get("metric_name") or "")
    value = _metric_value(row)
    for key in ("weakening_score", "weakness_score", "erosion_score"):
        explicit = _number(payload.get(key))
        if explicit is not None:
            return explicit
    if drift in {"DETERIORATING", "WEAKENING", "WEAKENED"}:
        return abs(value) if value is not None else float(_DRIFT_SEVERITY[drift])
    if value is not None and value < 0:
        return abs(value)
    if _contains_any(metric, ("weak", "deteriorat", "erosion", "decline")) and value is not None:
        return abs(value)
    return None


def _transition_label(row: Mapping[str, Any]) -> str | None:
    payload = _payload(row)
    transition = _clean(payload.get("stability_class_transition") or payload.get("transition"))
    if transition:
        return transition
    if row.get("metric_name") == "stability_class_transition":
        value = _clean(row.get("metric_value"))
        if value and not value.replace(".", "", 1).isdigit():
            return value
    return None


def _recurring_structures(row: Mapping[str, Any]) -> list[str]:
    payload = _payload(row)
    structures = payload.get("recurring_structures") or payload.get("morphologies") or payload.get("recurrent_structures") or []
    if isinstance(structures, str):
        structures = [structures]
    if not isinstance(structures, Sequence):
        structures = []
    if not structures and _contains_any(str(row.get("metric_name") or ""), ("recurr", "morphology")):
        structures = [_dimension(row)]
    return sorted({_clean(item).lower() for item in structures if _clean(item)})


def _build_items_from_scores(rows: Sequence[Mapping[str, Any]], score_fn: Callable[[Mapping[str, Any]], float | None], *, limit: int, metric_label: str) -> list[OrderedDict[str, Any]]:
    grouped: dict[str, list[tuple[float, Mapping[str, Any]]]] = defaultdict(list)
    for row in rows:
        score = score_fn(row)
        if score is None:
            continue
        grouped[_dimension(row)].append((float(score), row))
    items = []
    for identifier, scored_rows in grouped.items():
        scores = [score for score, _ in scored_rows]
        evidence_rows = [row for _, row in sorted(scored_rows, key=lambda item: _stable_row_key(item[1]))]
        evidence = [_supporting_evidence(row) for row in evidence_rows]
        fact_ids = sorted({_fact_id(row) for row in evidence_rows if _fact_id(row)})
        evidence_ids = sorted({_evidence_id(row) for row in evidence_rows if _evidence_id(row)})
        source_phases = sorted({_source_phase(row) for row in evidence_rows if _source_phase(row)})
        ranking_value = max(scores)
        items.append(OrderedDict([
            ("identifier", identifier),
            ("ranking_metric", OrderedDict([("name", metric_label), ("value", _round(ranking_value))])),
            ("supporting_fact_count", len(fact_ids)),
            ("supporting_fact_ids", fact_ids),
            ("supporting_evidence_ids", evidence_ids),
            ("supporting_evidence", evidence),
            ("source_phases", source_phases),
        ]))
    return sorted(items, key=lambda item: (-float(item["ranking_metric"]["value"] or 0), str(item["identifier"])))[:limit]


def _recurrent_items(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[OrderedDict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    snapshots: dict[str, set[str]] = defaultdict(set)
    for index, row in enumerate(rows):
        for structure in _recurring_structures(row):
            grouped[structure].append(row)
            snapshots[structure].add(str(row.get("window_days") or _time_key(row) or f"row_{index}"))
    items = []
    for identifier, evidence_rows in grouped.items():
        evidence_rows = sorted(evidence_rows, key=_stable_row_key)
        evidence = [_supporting_evidence(row) for row in evidence_rows]
        fact_ids = sorted({_fact_id(row) for row in evidence_rows if _fact_id(row)})
        evidence_ids = sorted({_evidence_id(row) for row in evidence_rows if _evidence_id(row)})
        items.append(OrderedDict([
            ("identifier", identifier),
            ("ranking_metric", OrderedDict([("name", "recurrence_count"), ("value", len(evidence_rows))])),
            ("supporting_fact_count", len(fact_ids)),
            ("supporting_fact_ids", fact_ids),
            ("supporting_evidence_ids", evidence_ids),
            ("supporting_evidence", evidence),
            ("source_phases", sorted({_source_phase(row) for row in evidence_rows if _source_phase(row)})),
            ("distinct_windows_or_snapshots", len(snapshots[identifier])),
        ]))
    return sorted(items, key=lambda item: (-int(item["ranking_metric"]["value"]), str(item["identifier"])))[:limit]


def _transition_items(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[OrderedDict[str, Any]]:
    expanded: list[tuple[str, Mapping[str, Any]]] = []
    for row in rows:
        payload = _payload(row)
        if row.get("metric_name") == "stability_class_transition" and isinstance(payload.get("transitions"), Mapping):
            for key, value in sorted(payload["transitions"].items()):
                label = _clean(value)
                if label:
                    synthetic = dict(row)
                    synthetic["entity_id"] = key
                    expanded.append((label, synthetic))
            continue
        label = _transition_label(row)
        if label:
            expanded.append((label, row))
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for label, row in expanded:
        grouped[label].append(row)
    items = []
    for identifier, evidence_rows in grouped.items():
        evidence_rows = sorted(evidence_rows, key=_stable_row_key)
        fact_ids = sorted({_fact_id(row) for row in evidence_rows if _fact_id(row)})
        evidence_ids = sorted({_evidence_id(row) for row in evidence_rows if _evidence_id(row)})
        items.append(OrderedDict([
            ("identifier", identifier),
            ("ranking_metric", OrderedDict([("name", "transition_count"), ("value", len(evidence_rows))])),
            ("supporting_fact_count", len(fact_ids)),
            ("supporting_fact_ids", fact_ids),
            ("supporting_evidence_ids", evidence_ids),
            ("supporting_evidence", [_supporting_evidence(row) for row in evidence_rows]),
            ("source_phases", sorted({_source_phase(row) for row in evidence_rows if _source_phase(row)})),
        ]))
    return sorted(items, key=lambda item: (-int(item["ranking_metric"]["value"]), str(item["identifier"])))[:limit]


def _governance_certification() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "OBS-QUERY-2"),
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


def _parameters(*, query_type: str, symbol: str | None, taxonomy: str | None, source_layer: str | None, snapshot_date: str | None, limit: int | None) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("query_type", query_type),
        ("symbol", symbol),
        ("taxonomy", taxonomy),
        ("source_layer", source_layer),
        ("snapshot_date", snapshot_date),
        ("limit", limit),
    ])


def retrieve_intelligence_question(
    *,
    query_type: str,
    client: Any | None = None,
    fact_rows: Iterable[Mapping[str, Any]] | None = None,
    symbol: str | None = None,
    taxonomy: str | None = None,
    source_layer: str | None = None,
    snapshot_date: str | date | datetime | None = None,
    limit: int | None = DEFAULT_LIMIT,
) -> OrderedDict[str, Any]:
    normalized_query_type = str(query_type).strip().lower()
    if normalized_query_type not in QUERY_TYPES:
        raise ValueError(f"query_type must be one of: {', '.join(QUERY_TYPES)}")
    safe_limit = bounded_limit(limit if limit is not None else DEFAULT_LIMIT)
    normalized_symbol = _clean(symbol).upper() if _clean(symbol) else None
    normalized_taxonomy = _clean(taxonomy)
    normalized_source_layer = _clean(source_layer)
    normalized_snapshot_date = _normalize_date(snapshot_date)
    rows = _load_rows(
        client=client,
        fact_rows=fact_rows,
        symbol=normalized_symbol,
        taxonomy=normalized_taxonomy,
        source_layer=normalized_source_layer,
        snapshot_date=normalized_snapshot_date,
        scan_limit=MAX_SCAN_ROWS,
    )

    if normalized_query_type == "persisted":
        items = _build_items_from_scores(rows, _persistence_score, limit=safe_limit, metric_label="persistence_score")
    elif normalized_query_type == "changed":
        items = _build_items_from_scores(rows, _change_score, limit=safe_limit, metric_label="change_ranking_score")
    elif normalized_query_type == "recurred":
        items = _recurrent_items(rows, limit=safe_limit)
    elif normalized_query_type == "dominant":
        items = _build_items_from_scores(rows, _dominance_score, limit=safe_limit, metric_label="dominance_score")
    elif normalized_query_type == "weakened":
        items = _build_items_from_scores(rows, _weakening_score, limit=safe_limit, metric_label="weakening_score")
    else:
        items = _transition_items(rows, limit=safe_limit)

    supporting_fact_ids = sorted({fact_id for item in items for fact_id in (item.get("supporting_fact_ids") or [])})
    supporting_evidence_ids = sorted({evidence_id for item in items for evidence_id in (item.get("supporting_evidence_ids") or [])})

    return OrderedDict([
        ("schema_version", "obs_query2_intelligence_question_v1"),
        ("source_table", OBSERVATION_FACTS_TABLE),
        ("query_type", normalized_query_type),
        ("query_parameters", _parameters(query_type=normalized_query_type, symbol=normalized_symbol, taxonomy=normalized_taxonomy, source_layer=normalized_source_layer, snapshot_date=normalized_snapshot_date, limit=limit)),
        ("parameters", _parameters(query_type=normalized_query_type, symbol=normalized_symbol, taxonomy=normalized_taxonomy, source_layer=normalized_source_layer, snapshot_date=normalized_snapshot_date, limit=limit)),
        ("row_count", len(items)),
        ("result_count", len(items)),
        ("hard_limit", HARD_LIMIT),
        ("effective_limit", safe_limit),
        ("result_items", items),
        ("results", items),
        ("supporting_fact_ids", supporting_fact_ids),
        ("supporting_evidence_ids", supporting_evidence_ids),
        ("governance_certification", _governance_certification()),
    ])


def get_persistent_structures(**kwargs: Any) -> OrderedDict[str, Any]:
    return retrieve_intelligence_question(query_type="persisted", **kwargs)


def get_changed_structures(**kwargs: Any) -> OrderedDict[str, Any]:
    return retrieve_intelligence_question(query_type="changed", **kwargs)


def get_recurrent_structures(**kwargs: Any) -> OrderedDict[str, Any]:
    return retrieve_intelligence_question(query_type="recurred", **kwargs)


def get_dominant_structures(**kwargs: Any) -> OrderedDict[str, Any]:
    return retrieve_intelligence_question(query_type="dominant", **kwargs)


def get_weakening_structures(**kwargs: Any) -> OrderedDict[str, Any]:
    return retrieve_intelligence_question(query_type="weakened", **kwargs)


def get_transitioning_structures(**kwargs: Any) -> OrderedDict[str, Any]:
    return retrieve_intelligence_question(query_type="transitioned", **kwargs)


def render_intelligence_question_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# OBS-QUERY-2 Intelligence Question Retrieval\n\n",
        "## Query summary\n",
        f"- query_type: {result.get('query_type')}\n",
        f"- source_table: {result.get('source_table')}\n",
        f"- result_count: {result.get('result_count', result.get('row_count'))}\n",
        f"- effective_limit: {result.get('effective_limit')}\n",
        f"- hard_limit: {result.get('hard_limit')}\n\n",
        "## Results table\n",
        "| identifier | ranking_metric | supporting_fact_count | source_phases |\n",
        "| --- | ---: | ---: | --- |\n",
    ]
    for item in result.get("results") or result.get("result_items") or []:
        metric = item.get("ranking_metric") or {}
        phases = ", ".join(item.get("source_phases") or [])
        lines.append(f"| {item.get('identifier') or ''} | {metric.get('name')}={metric.get('value')} | {item.get('supporting_fact_count')} | {phases} |\n")
    if not (result.get("results") or result.get("result_items")):
        lines.append("| none |  | 0 |  |\n")

    lines.append("\n## Supporting facts\n")
    fact_ids = result.get("supporting_fact_ids") or []
    if fact_ids:
        for fact_id in fact_ids:
            lines.append(f"- {fact_id}\n")
    else:
        lines.append("- none\n")

    lines.append("\n## Supporting evidence\n")
    evidence_ids = result.get("supporting_evidence_ids") or []
    if evidence_ids:
        for evidence_id in evidence_ids:
            lines.append(f"- {evidence_id}\n")
    else:
        lines.append("- none\n")

    lines.append("\n## Governance certification\n")
    for key, value in (result.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {value}\n")
    return "".join(lines)


def write_intelligence_question_outputs(result: Mapping[str, Any], *, output_json: str | Path | None = None, output_md: str | Path | None = None) -> OrderedDict[str, str | None]:
    json_path = Path(output_json) if output_json else None
    md_path = Path(output_md) if output_md else None
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_intelligence_question_markdown(result), encoding="utf-8")
    return OrderedDict([("output_json", str(json_path) if json_path else None), ("output_md", str(md_path) if md_path else None)])
