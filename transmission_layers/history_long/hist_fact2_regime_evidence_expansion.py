from __future__ import annotations

import json
from collections import Counter, OrderedDict, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from transmission_layers.history_long.hist_intel2_taxonomy_weighted_intelligence import CONFIDENCE_LABELS, taxonomy_for_fact

PHASE_ID = "HIST-FACT-2"
PHASE_NAME = "HIST-FACT-2_historical_regime_evidence_expansion"
SCHEMA_VERSION = "hist_fact2_v1"
DEFAULT_JSON_REPORT_PATH = "reports/hist_fact2_regime_evidence_expansion.json"
DEFAULT_MARKDOWN_REPORT_PATH = "reports/hist_fact2_regime_evidence_expansion.md"
DEFAULT_EXPANDED_EVIDENCE_PATH = "reports/hist_fact2_expanded_regime_evidence.json"
DEFAULT_FACT1_PATH = "reports/hist_fact1_expanded_observation_facts.json"
DEFAULT_INTEL2_PATH = "reports/hist_intel2_taxonomy_weighted_intelligence.json"
DEFAULT_INTEL3_PATH = "reports/hist_intel3_narrative_evolution.json"
DEFAULT_MAX_FACTS = 1000
MAX_FACT_ROWS = 7500
MIN_DELTA = 0.025
TRANSITION_PRESSURE_DELTA = 0.10
GOVERNANCE_CERTIFICATION: OrderedDict[str, bool] = OrderedDict(
    [
        ("analysis_only", True),
        ("local_only", True),
        ("no_provider_calls", True),
        ("no_supabase_writes", True),
        ("no_prediction", True),
        ("no_trading", True),
        ("no_portfolio_recommendation", True),
        ("no_governed_activation", True),
    ]
)

DIMENSION_TERMS: OrderedDict[str, tuple[str, ...]] = OrderedDict(
    [
        ("persistence", ("persistence", "persistent", "decay", "durable")),
        ("replay", ("replay", "recurrence", "density", "saturation")),
        ("concentration", ("concentration", "hhi", "share", "dominant", "leader_tail")),
        ("topology", ("topology", "coherence", "stability", "fragmentation", "morphology", "structural")),
        ("fragility", ("fragility", "fragile", "instability", "failed", "weak", "failure")),
        ("participation", ("breadth", "participation", "effective_symbol", "symbol_count", "symbol_share")),
    ]
)

DIRECTIONAL_FACT_TYPES: Mapping[str, tuple[str, str, str]] = {
    "persistence": ("persistence_acceleration_fact", "persistence_deceleration_fact", "persistence_inflection_fact"),
    "replay": ("replay_intensification_fact", "replay_dissipation_fact", "replay_inflection_fact"),
    "concentration": ("concentration_expansion_fact", "concentration_relaxation_fact", "concentration_inflection_fact"),
    "topology": ("topology_stabilization_fact", "topology_fragmentation_pressure_fact", "topology_inflection_fact"),
    "fragility": ("fragility_escalation_fact", "fragility_recovery_fact", "fragility_inflection_fact"),
    "participation": ("breadth_expansion_fact", "breadth_contraction_fact", "participation_shift_fact"),
}
TRANSITION_RELEVANT_FACT_TYPES = frozenset(
    set(ft for values in DIRECTIONAL_FACT_TYPES.values() for ft in values)
    | {"transition_pressure_fact", "transition_confirmation_fact", "transition_rejection_fact"}
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return "_".join(_text(value).lower().replace("-", "_").split())


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        for key in ("metric_value", "value", "score", "share", "density", "ratio", "count"):
            found = _number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round(value: Any) -> float | None:
    number = _number(value)
    return None if number is None else round(number, 6)


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb") or row.get("payload") or {}
    return payload if isinstance(payload, Mapping) else {}


def _window(row: Mapping[str, Any]) -> int | None:
    payload = _payload(row)
    for key in ("window_days", "window_trading_days", "window", "lookback_days"):
        value = row.get(key) if key in row else payload.get(key)
        number = _number(value)
        if number is not None:
            return int(number)
    return None


def _metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = _payload(row)
    for key in ("value", "score", "share", "density", "ratio", "count"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _evidence_count(row: Mapping[str, Any]) -> int:
    number = _number(row.get("evidence_count") or _payload(row).get("evidence_count"))
    return max(1, int(number)) if number is not None else 1


def _source_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _stable_id(parts: Sequence[Any]) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return f"histfact2_{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _confidence(source_fact_count: int, window_count: int, supporting_evidence_count: int) -> str:
    if source_fact_count <= 0 or window_count <= 0:
        return "INSUFFICIENT"
    if source_fact_count >= 2 and window_count >= 3 and supporting_evidence_count >= 3:
        return "HIGH"
    if source_fact_count >= 2 and window_count >= 2:
        return "MEDIUM"
    return "LOW"


def _bounded_payload(payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    ordered = OrderedDict((str(key), payload[key]) for key in sorted(payload, key=str))
    raw = json.dumps(ordered, sort_keys=True, default=str)
    if len(raw.encode("utf-8")) <= 4096:
        return ordered
    compact: OrderedDict[str, Any] = OrderedDict()
    for key, value in ordered.items():
        compact[key] = value if not isinstance(value, (list, dict)) else f"{type(value).__name__}[{len(value)}]"
    return compact


def _fact(
    *,
    fact_type: str,
    entity_type: str,
    entity_id: str,
    metric_name: str,
    metric_value: Any,
    window_days: int | None,
    evidence_count: int,
    confidence_label: str,
    source_phase: str,
    source_artifact: str,
    payload_jsonb: Mapping[str, Any],
) -> OrderedDict[str, Any]:
    row = OrderedDict(
        [
            ("phase_id", PHASE_ID),
            ("fact_type", _norm(fact_type)),
            ("entity_type", _norm(entity_type) or "regime_evidence"),
            ("entity_id", _norm(entity_id) or "ecosystem"),
            ("metric_name", _norm(metric_name)),
            ("metric_value", _round(metric_value)),
            ("window_days", window_days),
            ("evidence_count", int(max(0, evidence_count))),
            ("confidence_label", confidence_label if confidence_label in CONFIDENCE_LABELS else "LOW"),
            ("source_phase", source_phase),
            ("source_artifact", source_artifact),
            ("payload_jsonb", _bounded_payload(payload_jsonb)),
        ]
    )
    row["fact_id"] = _stable_id(
        [
            row["phase_id"],
            row["fact_type"],
            row["entity_type"],
            row["entity_id"],
            row["metric_name"],
            row["window_days"],
            json.dumps(row["payload_jsonb"], sort_keys=True, default=str),
        ]
    )
    return row


def _load_json(path: str | Path | None) -> tuple[Any, OrderedDict[str, Any]]:
    if not path:
        return None, OrderedDict([("path", None), ("status", "not_requested")])
    selected = Path(path)
    if not selected.exists():
        return None, OrderedDict([("path", selected.as_posix()), ("status", "missing")])
    payload = json.loads(selected.read_text(encoding="utf-8"))
    row_count = len(payload) if isinstance(payload, list) else len(payload.get("expanded_facts") or payload.get("expanded_regime_evidence") or []) if isinstance(payload, Mapping) else None
    status = OrderedDict([("path", selected.as_posix()), ("status", "loaded")])
    if row_count is not None:
        status["row_count"] = row_count
    if isinstance(payload, Mapping) and payload.get("phase_id"):
        status["phase_id"] = payload.get("phase_id")
    return payload, status


def _extract_fact_rows(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    if isinstance(payload, Mapping):
        for key in ("expanded_facts", "expanded_regime_evidence", "facts"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, Mapping)]
    return []


def _dimension(row: Mapping[str, Any]) -> str | None:
    haystack = " ".join(
        _norm(value)
        for value in (
            row.get("fact_type"),
            row.get("entity_type"),
            row.get("entity_id"),
            row.get("metric_name"),
            _payload(row).get("source_key"),
            _payload(row).get("section"),
            _payload(row).get("source_class"),
        )
    )
    matches = [dimension for dimension, terms in DIMENSION_TERMS.items() if any(term in haystack for term in terms)]
    if not matches:
        return None
    return sorted(set(matches), key=lambda item: list(DIMENSION_TERMS).index(item))[0]


def _entity_key(row: Mapping[str, Any], dimension: str) -> tuple[str, str]:
    entity_type = _norm(row.get("entity_type")) or "fact_entity"
    entity_id = _norm(row.get("entity_id")) or "unknown"
    if entity_type == "window" or entity_id.startswith("window_"):
        return "ecosystem", dimension
    return entity_type, entity_id


def _classify_rows(facts: Iterable[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    for index, row in enumerate(facts):
        if index >= MAX_FACT_ROWS or not isinstance(row, Mapping):
            break
        dimension = _dimension(row)
        value = _metric_value(row)
        window = _window(row)
        if dimension is None or value is None or window is None:
            continue
        taxonomy = taxonomy_for_fact(row)
        if taxonomy["tier"] == "C" and dimension != "participation":
            continue
        confidence = _text(row.get("confidence_label") or row.get("confidence")).upper() or "LOW"
        if confidence not in CONFIDENCE_LABELS:
            confidence = "LOW"
        entity_type, entity_id = _entity_key(row, dimension)
        rows.append(
            OrderedDict(
                [
                    ("index", index),
                    ("fact_id", row.get("fact_id") or _source_digest(row)),
                    ("dimension", dimension),
                    ("entity_type", entity_type),
                    ("entity_id", entity_id),
                    ("metric_name", _norm(row.get("metric_name")) or "metric_value"),
                    ("window_days", window),
                    ("metric_value", round(float(value), 6)),
                    ("evidence_count", _evidence_count(row)),
                    ("confidence_label", confidence),
                    ("source_phase", _text(row.get("source_phase")) or _text(row.get("phase_id"))),
                    ("source_artifact", _text(row.get("source_artifact"))),
                    ("taxonomy_tier", taxonomy["tier"]),
                    ("taxonomy_weight", taxonomy["weight"]),
                ]
            )
        )
    return rows


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _slope_inflects(values_by_window: Mapping[int, float]) -> bool:
    windows = sorted(values_by_window)
    if len(windows) < 3:
        return False
    slopes: list[float] = []
    for previous, current in zip(windows, windows[1:]):
        delta = values_by_window[current] - values_by_window[previous]
        if abs(delta) >= MIN_DELTA:
            slopes.append(delta)
    return any(a * b < 0 for a, b in zip(slopes, slopes[1:]))


def _directional_type(dimension: str, delta: float) -> str:
    positive, negative, inflection = DIRECTIONAL_FACT_TYPES[dimension]
    if abs(delta) < MIN_DELTA:
        return inflection
    return positive if delta > 0 else negative


def _build_regime_facts(rows: Sequence[Mapping[str, Any]], fact1_artifact: str, intel3_artifact: str, intel3_payload: Mapping[str, Any] | None) -> list[OrderedDict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["dimension"]), str(row["entity_type"]), str(row["entity_id"]), str(row["metric_name"]))].append(row)

    facts: list[OrderedDict[str, Any]] = []
    for (dimension, entity_type, entity_id, metric_name), group in sorted(grouped.items()):
        by_window: OrderedDict[int, list[Mapping[str, Any]]] = OrderedDict()
        for row in sorted(group, key=lambda item: (int(item["window_days"]), int(item["index"]))):
            by_window.setdefault(int(row["window_days"]), []).append(row)
        if len(by_window) < 2:
            continue
        values_by_window = OrderedDict((window, _mean([float(item["metric_value"]) for item in items])) for window, items in by_window.items())
        windows = list(values_by_window)
        start_window, end_window = windows[0], windows[-1]
        start_value, end_value = values_by_window[start_window], values_by_window[end_window]
        delta = end_value - start_value
        source_fact_ids = sorted({str(item["fact_id"]) for item in group})
        source_phases = sorted({str(item["source_phase"]) for item in group if item.get("source_phase")})
        source_artifacts = sorted({str(item["source_artifact"]) for item in group if item.get("source_artifact")})
        source_fact_count = len(source_fact_ids)
        evidence_count = sum(int(item["evidence_count"]) for item in group)
        confidence = _confidence(source_fact_count, len(windows), evidence_count)
        fact_type = _directional_type(dimension, delta)
        if _slope_inflects(values_by_window):
            fact_type = DIRECTIONAL_FACT_TYPES[dimension][2]
        facts.append(
            _fact(
                fact_type=fact_type,
                entity_type=entity_type,
                entity_id=entity_id,
                metric_name=f"{metric_name}_window_delta",
                metric_value=delta,
                window_days=end_window,
                evidence_count=evidence_count,
                confidence_label=confidence,
                source_phase="HIST-FACT-1",
                source_artifact=fact1_artifact,
                payload_jsonb={
                    "dimension": dimension,
                    "source_metric_name": metric_name,
                    "start_window_days": start_window,
                    "end_window_days": end_window,
                    "start_value": round(start_value, 6),
                    "end_value": round(end_value, 6),
                    "absolute_delta": round(abs(delta), 6),
                    "window_count": len(windows),
                    "source_fact_count": source_fact_count,
                    "source_fact_ids": source_fact_ids[:25],
                    "source_phases": source_phases,
                    "source_artifacts": source_artifacts[:10],
                    "evidence_role": "regime_transition_evidence",
                },
            )
        )
        if abs(delta) >= TRANSITION_PRESSURE_DELTA:
            facts.append(
                _fact(
                    fact_type="transition_pressure_fact",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    metric_name=f"{dimension}_{metric_name}_transition_pressure",
                    metric_value=abs(delta),
                    window_days=end_window,
                    evidence_count=evidence_count,
                    confidence_label=confidence,
                    source_phase="HIST-FACT-1",
                    source_artifact=fact1_artifact,
                    payload_jsonb={
                        "dimension": dimension,
                        "source_metric_name": metric_name,
                        "directional_fact_type": fact_type,
                        "start_window_days": start_window,
                        "end_window_days": end_window,
                        "window_count": len(windows),
                        "source_fact_count": source_fact_count,
                        "source_fact_ids": source_fact_ids[:25],
                        "evidence_role": "transition_readiness_evidence",
                    },
                )
            )

    diagnostics = (intel3_payload or {}).get("transition_diagnostics") if isinstance(intel3_payload, Mapping) else None
    if isinstance(diagnostics, Mapping):
        found = int(_number(diagnostics.get("candidate_transitions_found")) or 0)
        emitted = int(_number(diagnostics.get("candidate_transitions_emitted")) or 0)
        if found > emitted:
            confidence = _confidence(found, 1, found)
            facts.append(
                _fact(
                    fact_type="transition_rejection_fact",
                    entity_type="ecosystem",
                    entity_id="candidate_transition_filter",
                    metric_name="candidate_transitions_found_minus_emitted",
                    metric_value=found - emitted,
                    window_days=None,
                    evidence_count=found,
                    confidence_label=confidence,
                    source_phase="HIST-INTEL-3",
                    source_artifact=intel3_artifact,
                    payload_jsonb={
                        "source_phase": "HIST-INTEL-3",
                        "candidate_transitions_found": found,
                        "candidate_transitions_emitted": emitted,
                        "evidence_role": "transition_readiness_evidence",
                        "reason": "candidate_transition_evidence_below_emission_threshold",
                    },
                )
            )
        if emitted > 0:
            facts.append(
                _fact(
                    fact_type="transition_confirmation_fact",
                    entity_type="ecosystem",
                    entity_id="candidate_transition_filter",
                    metric_name="candidate_transitions_emitted",
                    metric_value=emitted,
                    window_days=None,
                    evidence_count=emitted,
                    confidence_label=_confidence(emitted, 2, emitted),
                    source_phase="HIST-INTEL-3",
                    source_artifact=intel3_artifact,
                    payload_jsonb={"source_phase": "HIST-INTEL-3", "candidate_transitions_emitted": emitted, "evidence_role": "transition_readiness_evidence"},
                )
            )
    return facts


def _dedupe_and_bound(rows: Iterable[OrderedDict[str, Any]], max_facts: int) -> list[OrderedDict[str, Any]]:
    unique: dict[str, OrderedDict[str, Any]] = {}
    for row in rows:
        unique.setdefault(str(row["fact_id"]), row)
    ordered = sorted(
        unique.values(),
        key=lambda row: (
            row["fact_type"],
            row["entity_type"],
            row["entity_id"],
            row["metric_name"],
            row["window_days"] is None,
            row["window_days"] or -1,
            row["fact_id"],
        ),
    )
    return ordered[: max(0, int(max_facts))]


def build_hist_fact2_expansion(
    *,
    fact1_path: str | Path | None = DEFAULT_FACT1_PATH,
    intel2_path: str | Path | None = DEFAULT_INTEL2_PATH,
    intel3_path: str | Path | None = DEFAULT_INTEL3_PATH,
    observation_facts: Iterable[Mapping[str, Any]] | None = None,
    max_facts: int = DEFAULT_MAX_FACTS,
) -> OrderedDict[str, Any]:
    fact1_payload, fact1_status = _load_json(fact1_path) if observation_facts is None else (None, OrderedDict([("path", None), ("status", "supplied")]))
    intel2_payload, intel2_status = _load_json(intel2_path)
    intel3_payload, intel3_status = _load_json(intel3_path)
    source_rows = list(observation_facts or _extract_fact_rows(fact1_payload))
    classified = _classify_rows(source_rows)
    fact1_artifact = fact1_status.get("path") or "supplied_observation_facts"
    intel3_artifact = intel3_status.get("path") or "hist_intel3_not_loaded"
    facts = _dedupe_and_bound(_build_regime_facts(classified, str(fact1_artifact), str(intel3_artifact), intel3_payload if isinstance(intel3_payload, Mapping) else None), max_facts)
    fact_type_distribution = OrderedDict(sorted(Counter(row["fact_type"] for row in facts).items()))
    confidence_distribution = OrderedDict(sorted(Counter(row["confidence_label"] for row in facts).items()))
    multi_window_fact_count = sum(1 for row in facts if int((row.get("payload_jsonb") or {}).get("window_count") or 0) >= 2)
    transition_relevant_fact_count = sum(1 for row in facts if row.get("fact_type") in TRANSITION_RELEVANT_FACT_TYPES)
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("phase_id", PHASE_ID),
            ("phase_name", PHASE_NAME),
            ("status", "ok" if facts else "limited"),
            ("source_digest", _source_digest({"source_rows": source_rows, "intel2_status": intel2_status, "intel3_status": intel3_status})),
            ("governance_certification", GOVERNANCE_CERTIFICATION.copy()),
            ("input_status", OrderedDict([("hist_fact1", fact1_status), ("hist_intel2", intel2_status), ("hist_intel3", intel3_status)])),
            ("source_fact_count", len(source_rows)),
            ("eligible_source_fact_count", len(classified)),
            ("expanded_fact_count", len(facts)),
            ("net_new_fact_count", len(facts)),
            ("max_facts", int(max_facts)),
            ("bounded_output", len(facts) <= int(max_facts)),
            ("fact_type_distribution", fact_type_distribution),
            ("confidence_distribution", confidence_distribution),
            ("transition_relevant_fact_count", transition_relevant_fact_count),
            ("multi_window_fact_count", multi_window_fact_count),
            ("expanded_regime_evidence", facts),
        ]
    )


def build_markdown_report(report: Mapping[str, Any]) -> str:
    lines = ["# HIST-FACT-2 — Historical Regime Evidence Expansion\n\n", "## Governance Certification\n"]
    for key, value in (report.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {str(value).lower()}\n")
    lines.extend(
        [
            "\n## Metrics\n",
            f"- source_fact_count: {report.get('source_fact_count')}\n",
            f"- eligible_source_fact_count: {report.get('eligible_source_fact_count')}\n",
            f"- expanded_fact_count: {report.get('expanded_fact_count')}\n",
            f"- net_new_fact_count: {report.get('net_new_fact_count')}\n",
            f"- transition_relevant_fact_count: {report.get('transition_relevant_fact_count')}\n",
            f"- multi_window_fact_count: {report.get('multi_window_fact_count')}\n",
            f"- bounded_output: {str(report.get('bounded_output')).lower()}\n",
            "\n## Fact Type Distribution\n",
        ]
    )
    for key, value in (report.get("fact_type_distribution") or {}).items():
        lines.append(f"- {key}: {value}\n")
    lines.append("\n## Confidence Distribution\n")
    for key, value in (report.get("confidence_distribution") or {}).items():
        lines.append(f"- {key}: {value}\n")
    lines.append("\n## Boundary Statement\n")
    lines.append("HIST-FACT-2 is a deterministic local fact-generation layer. It emits evidence facts only and does not call providers, write Supabase, ingest live data, predict, trade, recommend portfolios, or activate governed workflows.\n")
    return "".join(lines)


def run_hist_fact2_expansion(
    *,
    fact1_path: str | Path | None = DEFAULT_FACT1_PATH,
    intel2_path: str | Path | None = DEFAULT_INTEL2_PATH,
    intel3_path: str | Path | None = DEFAULT_INTEL3_PATH,
    json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH,
    markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH,
    expanded_evidence_path: str | Path = DEFAULT_EXPANDED_EVIDENCE_PATH,
    max_facts: int = DEFAULT_MAX_FACTS,
) -> OrderedDict[str, Any]:
    report = build_hist_fact2_expansion(fact1_path=fact1_path, intel2_path=intel2_path, intel3_path=intel3_path, max_facts=max_facts)
    json_path = Path(json_report_path)
    md_path = Path(markdown_report_path)
    evidence_path = Path(expanded_evidence_path)
    for path in (json_path, md_path, evidence_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    evidence_path.write_text(json.dumps(report["expanded_regime_evidence"], indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown_report(report), encoding="utf-8")
    return report
