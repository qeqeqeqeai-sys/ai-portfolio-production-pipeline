from __future__ import annotations

import json
from collections import OrderedDict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

OBSERVATION_FACTS_TABLE = "sefi_observation_facts"
DEFAULT_LIMIT = 100
HARD_LIMIT = 500

READ_COLUMNS = (
    "id,phase_id,phase_name,window_days,entity_type,entity_id,metric_name,metric_value,"
    "artifact_id,run_id,created_at,loaded_at,payload_jsonb,duplicate_prevention_key"
)

SUPPORTED_COLUMN_FILTERS = OrderedDict([
    ("source_layer", "phase_id"),
    ("taxonomy", "metric_name"),
    ("evidence_id", "id"),
])

UNSUPPORTED_FILTER_REASONS = {
    "sector": "sefi_observation_facts has no sector column in DB-2 OBS-QUERY-1 schema.",
    "subsector": "sefi_observation_facts has no subsector column in DB-2 OBS-QUERY-1 schema.",
    "min_confidence": "sefi_observation_facts has no confidence or strength column in DB-2 OBS-QUERY-1 schema.",
}


def bounded_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    return max(0, min(int(limit), HARD_LIMIT))


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _date_prefix(value: Any) -> str:
    text = str(value or "")
    return text[:10]


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
    # Keep validation deterministic and lightweight; ISO date is the public CLI contract.
    return datetime.strptime(text[:10], "%Y-%m-%d").date().isoformat()


def _execute(query: Any) -> list[Mapping[str, Any]]:
    result = query.execute()
    data = getattr(result, "data", result)
    return [row for row in (data or []) if isinstance(row, Mapping)]


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
    value = _clean(payload.get("fact_id") or payload.get("evidence_id"))
    if value:
        return value
    return ""


def _stable_row_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("loaded_at") or row.get("created_at") or ""),
        str(row.get("run_id") or ""),
        str(row.get("phase_id") or ""),
        str(row.get("entity_type") or ""),
        str(row.get("entity_id") or ""),
        _fact_id(row),
    )


def _canonical_fact(row: Mapping[str, Any]) -> OrderedDict[str, Any]:
    payload = _payload(row)
    evidence_id = _clean(payload.get("evidence_id") or row.get("id") or row.get("duplicate_prevention_key"))
    return OrderedDict([
        ("fact_id", _fact_id(row)),
        ("evidence_id", evidence_id),
        ("snapshot_date", _date_prefix(row.get("loaded_at") or row.get("created_at"))),
        ("phase_id", row.get("phase_id")),
        ("phase_name", row.get("phase_name")),
        ("window_days", row.get("window_days")),
        ("entity_type", row.get("entity_type")),
        ("entity_id", row.get("entity_id")),
        ("symbol", _row_symbol(row)),
        ("taxonomy", row.get("metric_name")),
        ("metric_name", row.get("metric_name")),
        ("metric_value", row.get("metric_value")),
        ("artifact_id", row.get("artifact_id")),
        ("run_id", row.get("run_id")),
        ("created_at", row.get("created_at")),
        ("loaded_at", row.get("loaded_at")),
        ("payload_jsonb", payload),
    ])


def _governance_certification() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "OBS-QUERY-1"),
        ("retrieval_only", True),
        ("no_synthesis", True),
        ("no_new_intelligence_generation", True),
        ("provider_api_calls_enabled", False),
        ("db_writes_enabled", False),
        ("schema_migrations_enabled", False),
        ("trading_or_portfolio_action_language_enabled", False),
        ("predictions_enabled", False),
        ("recommendations_enabled", False),
        ("source_of_truth", OBSERVATION_FACTS_TABLE),
    ])


def _requested_parameters(**kwargs: Any) -> OrderedDict[str, Any]:
    keys = [
        "snapshot_date",
        "symbol",
        "sector",
        "subsector",
        "taxonomy",
        "source_layer",
        "min_confidence",
        "evidence_id",
        "limit",
    ]
    return OrderedDict((key, kwargs.get(key)) for key in keys)


def _unsupported_filters(*, sector: Any = None, subsector: Any = None, min_confidence: Any = None) -> list[OrderedDict[str, Any]]:
    unsupported = []
    for key, value in (("sector", sector), ("subsector", subsector), ("min_confidence", min_confidence)):
        if value is not None and str(value).strip() != "":
            unsupported.append(OrderedDict([("filter", key), ("value", value), ("reason", UNSUPPORTED_FILTER_REASONS[key])]))
    return unsupported


def _apply_local_filters(
    rows: Iterable[Mapping[str, Any]],
    *,
    snapshot_date: str | None,
    symbol: str | None,
    source_layer: str | None,
    taxonomy: str | None,
    evidence_id: str | None,
) -> list[Mapping[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    for row in rows:
        if snapshot_date and _date_prefix(row.get("loaded_at") or row.get("created_at")) != snapshot_date:
            continue
        if symbol and _row_symbol(row) != symbol.upper():
            continue
        if source_layer and row.get("phase_id") != source_layer:
            continue
        if taxonomy and row.get("metric_name") != taxonomy:
            continue
        if evidence_id and _fact_id(row) != str(evidence_id):
            payload = _payload(row)
            if str(payload.get("evidence_id") or "") != str(evidence_id):
                continue
        selected.append(row)
    return sorted(selected, key=_stable_row_key)


def retrieve_observation_facts(
    *,
    client: Any | None = None,
    fact_rows: Iterable[Mapping[str, Any]] | None = None,
    snapshot_date: str | date | datetime | None = None,
    symbol: str | None = None,
    sector: str | None = None,
    subsector: str | None = None,
    taxonomy: str | None = None,
    source_layer: str | None = None,
    min_confidence: float | None = None,
    evidence_id: str | int | None = None,
    limit: int | None = DEFAULT_LIMIT,
) -> OrderedDict[str, Any]:
    """Retrieve bounded DB-2 observation facts without synthesis or writes."""
    safe_limit = bounded_limit(limit)
    normalized_snapshot_date = _normalize_date(snapshot_date)
    normalized_symbol = _clean(symbol).upper() if _clean(symbol) else None
    normalized_taxonomy = _clean(taxonomy)
    normalized_source_layer = _clean(source_layer)
    normalized_evidence_id = _clean(evidence_id)

    applied_filters: list[OrderedDict[str, Any]] = []
    unsupported_filters = _unsupported_filters(sector=sector, subsector=subsector, min_confidence=min_confidence)

    if normalized_snapshot_date:
        applied_filters.append(OrderedDict([("filter", "snapshot_date"), ("field", "loaded_at_date"), ("value", normalized_snapshot_date), ("behavior", "safe date-prefix filter on loaded_at/created_at")]))
    if normalized_symbol:
        applied_filters.append(OrderedDict([("filter", "symbol"), ("field", "entity_id when entity_type=symbol; payload symbol/ticker for local post-filter"), ("value", normalized_symbol)]))
    if normalized_source_layer:
        applied_filters.append(OrderedDict([("filter", "source_layer"), ("field", "phase_id"), ("value", normalized_source_layer)]))
    if normalized_taxonomy:
        applied_filters.append(OrderedDict([("filter", "taxonomy"), ("field", "metric_name"), ("value", normalized_taxonomy)]))
    if normalized_evidence_id:
        applied_filters.append(OrderedDict([("filter", "evidence_id"), ("field", "id/fact_id/duplicate_prevention_key or payload evidence_id"), ("value", normalized_evidence_id)]))

    if client is not None:
        query = client.table(OBSERVATION_FACTS_TABLE).select(READ_COLUMNS)
        if normalized_source_layer:
            query = query.eq("phase_id", normalized_source_layer)
        if normalized_taxonomy:
            query = query.eq("metric_name", normalized_taxonomy)
        if normalized_symbol:
            query = query.eq("entity_type", "symbol").eq("entity_id", normalized_symbol)
        if normalized_snapshot_date and hasattr(query, "gte") and hasattr(query, "lt"):
            start = f"{normalized_snapshot_date}T00:00:00Z"
            end = f"{(datetime.strptime(normalized_snapshot_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()}T00:00:00Z"
            query = query.gte("loaded_at", start).lt("loaded_at", end)
        if normalized_evidence_id and normalized_evidence_id.isdigit():
            query = query.eq("id", int(normalized_evidence_id))
        elif normalized_evidence_id:
            query = query.eq("duplicate_prevention_key", normalized_evidence_id)
        query = query.order("loaded_at", desc=False).order("run_id", desc=False).order("id", desc=False).limit(safe_limit)
        raw_rows = _execute(query)
    else:
        raw_rows = [row for row in (fact_rows or []) if isinstance(row, Mapping)]

    filtered_rows = _apply_local_filters(
        raw_rows,
        snapshot_date=normalized_snapshot_date,
        symbol=normalized_symbol,
        source_layer=normalized_source_layer,
        taxonomy=normalized_taxonomy,
        evidence_id=normalized_evidence_id,
    )[:safe_limit]
    facts = [_canonical_fact(row) for row in filtered_rows]
    evidence_references = [
        OrderedDict([
            ("evidence_id", fact.get("evidence_id")),
            ("fact_id", fact.get("fact_id")),
            ("artifact_id", fact.get("artifact_id")),
            ("run_id", fact.get("run_id")),
        ])
        for fact in facts
        if fact.get("evidence_id") or fact.get("artifact_id") or fact.get("run_id")
    ]

    return OrderedDict([
        ("schema_version", "obs_query1_fact_retrieval_v1"),
        ("source_table", OBSERVATION_FACTS_TABLE),
        ("query_parameters", _requested_parameters(snapshot_date=normalized_snapshot_date, symbol=normalized_symbol, sector=sector, subsector=subsector, taxonomy=normalized_taxonomy, source_layer=normalized_source_layer, min_confidence=min_confidence, evidence_id=normalized_evidence_id, limit=limit)),
        ("applied_filters", applied_filters),
        ("unsupported_filters", unsupported_filters),
        ("row_count", len(facts)),
        ("hard_limit", HARD_LIMIT),
        ("effective_limit", safe_limit),
        ("facts", facts),
        ("evidence_references", evidence_references),
        ("governance_certification", _governance_certification()),
    ])


def render_observation_fact_retrieval_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# OBS-QUERY-1 Observation Fact Retrieval\n\n",
        "## Query summary\n",
        f"- source_table: {result.get('source_table')}\n",
        f"- row_count: {result.get('row_count')}\n",
        f"- effective_limit: {result.get('effective_limit')}\n",
        f"- hard_limit: {result.get('hard_limit')}\n\n",
        "## Applied filters\n",
    ]
    applied = result.get("applied_filters") or []
    if applied:
        for item in applied:
            lines.append(f"- {item.get('filter')}: {item.get('field')} = {item.get('value')}\n")
    else:
        lines.append("- none\n")
    lines.append("\n## Unsupported filters\n")
    unsupported = result.get("unsupported_filters") or []
    if unsupported:
        for item in unsupported:
            lines.append(f"- {item.get('filter')}: {item.get('value')} ({item.get('reason')})\n")
    else:
        lines.append("- none\n")

    lines.append("\n## Retrieved fact table\n")
    lines.append("| fact_id | snapshot_date | phase_id | entity_type | entity_id | taxonomy | metric_value | artifact_id | run_id |\n")
    lines.append("| --- | --- | --- | --- | --- | --- | ---: | --- | --- |\n")
    for fact in result.get("facts") or []:
        lines.append(
            "| {fact_id} | {snapshot_date} | {phase_id} | {entity_type} | {entity_id} | {taxonomy} | {metric_value} | {artifact_id} | {run_id} |\n".format(
                fact_id=fact.get("fact_id") or "",
                snapshot_date=fact.get("snapshot_date") or "",
                phase_id=fact.get("phase_id") or "",
                entity_type=fact.get("entity_type") or "",
                entity_id=fact.get("entity_id") or "",
                taxonomy=fact.get("taxonomy") or "",
                metric_value="" if fact.get("metric_value") is None else fact.get("metric_value"),
                artifact_id=fact.get("artifact_id") or "",
                run_id=fact.get("run_id") or "",
            )
        )

    lines.append("\n## Evidence references\n")
    evidence = result.get("evidence_references") or []
    if evidence:
        for item in evidence:
            lines.append(f"- evidence_id={item.get('evidence_id')} fact_id={item.get('fact_id')} artifact_id={item.get('artifact_id')} run_id={item.get('run_id')}\n")
    else:
        lines.append("- none available\n")

    lines.append("\n## Governance certification\n")
    for key, value in (result.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {value}\n")
    return "".join(lines)


def write_observation_fact_retrieval_outputs(result: Mapping[str, Any], *, output_json: str | Path | None = None, output_md: str | Path | None = None) -> OrderedDict[str, str | None]:
    json_path = Path(output_json) if output_json else None
    md_path = Path(output_md) if output_md else None
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_observation_fact_retrieval_markdown(result), encoding="utf-8")
    return OrderedDict([("output_json", str(json_path) if json_path else None), ("output_md", str(md_path) if md_path else None)])
