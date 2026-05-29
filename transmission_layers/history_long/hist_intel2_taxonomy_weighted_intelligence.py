from __future__ import annotations

import json
from collections import Counter, OrderedDict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

PHASE_ID = "HIST-INTEL-2"
PHASE_NAME = "HIST-INTEL-2_taxonomy_weighted_intelligence_engine"
SCHEMA_VERSION = "hist_intel2_v1"
DEFAULT_JSON_REPORT_PATH = "reports/hist_intel2_taxonomy_weighted_intelligence.json"
DEFAULT_MARKDOWN_REPORT_PATH = "reports/hist_intel2_taxonomy_weighted_intelligence.md"
DEFAULT_EXPANDED_FACTS_PATH = "reports/hist_fact1_expanded_observation_facts.json"
DEFAULT_TOP_N = 10
MAX_TOP_N = 10
MAX_FACT_ROWS = 7500
CONFIDENCE_LABELS = ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT")

TIER_A_WEIGHT = 3.0
TIER_B_WEIGHT = 1.5
TIER_C_WEIGHT = 0.1

TIER_A_FACT_TYPES = frozenset(
    {
        "structural_anchor_fact",
        "structural_hub_fact",
        "structural_transition_fact",
        "topology_stability_fact",
        "topology_coherence_fact",
        "topology_fragmentation_fact",
        "topology_persistence_fact",
        "sector_concentration_fact",
        "subsector_concentration_fact",
        "replay_density_fact",
        "replay_recurrence_fact",
        "replay_stability_fact",
        "persistence_fact",
        "persistence_decay_fact",
        "sector_persistence_fact",
        "subsector_persistence_fact",
        "fragility_fact",
        "breadth_fragility_fact",
        "sector_fragility_fact",
        "subsector_fragility_fact",
        "structural_instability_fact",
        "morphology_drift_fact",
    }
)

TIER_C_FACT_TYPES = frozenset(
    {
        "pipeline_diagnostic_fact",
        "provider_degradation_fact",
        "ingestion_continuity_fact",
        "normalization_diagnostic_fact",
        "reconciliation_diagnostic_fact",
        "artifact_diagnostic_fact",
    }
)

OPERATIONAL_METRICS = frozenset(
    {
        "normalized_rows",
        "reconciled_date_ratio",
        "classification_code",
        "absolute_delta",
        "endpoint_failure_count",
        "partial_count",
        "exact_date_match_ratio",
        "completeness_ratio",
        "effective_symbol_count",
        "provider_degradation",
        "provider_degradation_count",
        "failed_count",
        "row_count",
        "rows_loaded",
        "records_loaded",
        "loaded_rows",
        "input_rows",
        "output_rows",
        "artifact_count",
        "missing_sources",
        "runtime_seconds",
        "schema_version",
        "ingestion_continuity_ratio",
        "continuity_gap_count",
    }
)

ALLOWED_ECOSYSTEM_METRIC_ENTITIES = frozenset(
    {
        "replay_density",
        "replay_saturation",
        "topology_richness",
        "morphology_persistence",
        "concentration_stability_drift",
    }
)

OPERATIONAL_ENTITY_TYPES = frozenset({"pipeline", "diagnostic", "artifact", "schema"})

OPERATIONAL_TERMS = (
    "normalized",
    "reconciled",
    "failed_count",
    "provider_degradation",
    "ingestion_continuity",
    "continuity_gap",
    "diagnostic",
    "pipeline",
    "artifact",
    "schema",
    "runtime",
    "loaded_rows",
    "row_count",
)

CATEGORY_FACT_TERMS: OrderedDict[str, tuple[str, ...]] = OrderedDict(
    [
        ("hubs", ("structural_hub", "hub", "centrality", "leader", "importance")),
        ("anchors", ("structural_anchor", "anchor", "stability", "stable", "coherence", "coherent", "topology_stability", "topology_coherence")),
        ("replay", ("replay", "recurrence", "recurring", "density")),
        ("persistence", ("persistence", "persistent", "cross_window", "durable")),
        ("fragility", ("fragility", "fragile", "instability", "unstable", "weak", "breadth_fragility", "fragmentation")),
        ("drift", ("drift", "morphology", "transition", "delta", "change", "decay", "deteriorating", "churn")),
        ("topology", ("topology", "fragmentation", "coherence", "morphology", "structural")),
    ]
)

SCORE_KEYS = {
    "hubs": "hub_score",
    "anchors": "anchor_score",
    "replay": "replay_score",
    "persistence": "persistence_score",
    "fragility": "fragility_score",
    "drift": "drift_score",
    "topology": "topology_score",
}


def governance_certification() -> OrderedDict[str, bool]:
    return OrderedDict(
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
        for key in ("metric_value", "value", "score", "share", "density", "ratio", "persistence_score", "stability_score", "centrality_score", "fragility_score", "drift_score", "replay_density"):
            found = _number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _bounded_top_n(top_n: int | None) -> int:
    return max(0, min(int(top_n if top_n is not None else DEFAULT_TOP_N), MAX_TOP_N))


def _source_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb") or row.get("payload")
    return payload if isinstance(payload, Mapping) else {}


def _window(row: Mapping[str, Any]) -> str | None:
    payload = _payload(row)
    value = row.get("window_days") or row.get("window_trading_days") or row.get("window") or payload.get("window_days")
    return None if value in (None, "") else str(value)


def _metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = _payload(row)
    for key in ("persistence_score", "stability_score", "centrality_score", "fragility_score", "drift_score", "replay_density", "score", "value"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _fact_text(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    payload_bits = " ".join(_text(payload.get(key)) for key in sorted(payload, key=str) if key in {"dimension", "structure", "class", "stability_class", "drift_class", "fragility_class", "label", "section", "source_class"})
    return " ".join(
        [
            _text(row.get("phase_id")),
            _text(row.get("source_phase")),
            _text(row.get("fact_type")),
            _text(row.get("entity_type")),
            _text(row.get("entity_id")),
            _text(row.get("metric_name")),
            payload_bits,
        ]
    ).lower()


def _is_operational_dimension(value: Any) -> bool:
    normalized = _norm(value)
    return bool(normalized) and (normalized in OPERATIONAL_METRICS or any(term in normalized for term in OPERATIONAL_TERMS))


def _is_allowed_ecosystem_metric_entity(row: Mapping[str, Any], fact_type: str, metric: str) -> bool:
    if _norm(row.get("entity_type")) != "metric":
        return True
    entity_id = _entity_name(row)
    return entity_id in ALLOWED_ECOSYSTEM_METRIC_ENTITIES and fact_type in TIER_A_FACT_TYPES and metric not in OPERATIONAL_METRICS and not _is_operational_dimension(metric)


def taxonomy_for_fact(row: Mapping[str, Any]) -> OrderedDict[str, Any]:
    fact_type = _norm(row.get("fact_type"))
    metric = _norm(row.get("metric_name"))
    entity_type = _norm(row.get("entity_type"))
    entity_id = _entity_name(row)
    text = _fact_text(row)
    operational = (
        fact_type in TIER_C_FACT_TYPES
        or metric in OPERATIONAL_METRICS
        or entity_id in OPERATIONAL_METRICS
        or entity_type in OPERATIONAL_ENTITY_TYPES
        or _is_operational_dimension(metric)
        or _is_operational_dimension(entity_id)
        or _is_operational_dimension(entity_type)
        or not _is_allowed_ecosystem_metric_entity(row, fact_type, metric)
    )
    if operational:
        tier = "C"
        weight = TIER_C_WEIGHT
        rationale = "operational/pipeline telemetry suppressed from executive ecosystem intelligence"
    elif fact_type in TIER_A_FACT_TYPES or any(term in text for terms in CATEGORY_FACT_TERMS.values() for term in terms):
        tier = "A"
        weight = TIER_A_WEIGHT
        rationale = "ecosystem intelligence fact prioritized for executive findings"
    else:
        tier = "B"
        weight = TIER_B_WEIGHT
        rationale = "supporting ecosystem context retained below Tier A priority"
    return OrderedDict([("tier", tier), ("weight", weight), ("rationale", rationale)])


def _categories(row: Mapping[str, Any]) -> list[str]:
    text = _fact_text(row)
    categories = [category for category, terms in CATEGORY_FACT_TERMS.items() if any(term in text for term in terms)]
    if not categories and taxonomy_for_fact(row)["tier"] == "B":
        categories = ["topology"]
    return sorted(set(categories))


def _entity_name(row: Mapping[str, Any]) -> str:
    payload = _payload(row)
    for key in ("entity_id", "dimension", "structure", "sector", "subsector", "symbol", "group", "name"):
        value = row.get(key) if key in row else payload.get(key)
        if _text(value):
            return _norm(value)
    return _norm(row.get("metric_name") or "unknown")


def _raw_evidence_count(row: Mapping[str, Any]) -> int:
    value = row.get("evidence_count") or row.get("evidence") or _payload(row).get("evidence_count")
    number = _number(value)
    return max(1, int(number)) if number is not None else 1


def _confidence_points(label: str | None) -> float:
    return {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4, "INSUFFICIENT": 0.1}.get(_text(label).upper(), 0.4)


def _confidence_label(evidence_count: int, window_coverage: int, phase_coverage: int, recurrence_count: int, confidence_points: float) -> str:
    if evidence_count <= 0:
        return "INSUFFICIENT"
    if confidence_points >= 0.8 and (window_coverage >= 2 or phase_coverage >= 2 or evidence_count >= 3 or recurrence_count >= 2):
        return "HIGH"
    if confidence_points >= 0.55 or evidence_count >= 2 or window_coverage >= 2:
        return "MEDIUM"
    return "LOW"


def _classify_facts(facts: Iterable[Mapping[str, Any]], max_fact_rows: int) -> tuple[list[OrderedDict[str, Any]], list[OrderedDict[str, Any]], OrderedDict[str, int]]:
    ecosystem: list[OrderedDict[str, Any]] = []
    diagnostics: list[OrderedDict[str, Any]] = []
    tier_counts: Counter[str] = Counter()
    for index, row in enumerate(facts):
        if index >= max(0, min(int(max_fact_rows), MAX_FACT_ROWS)):
            break
        if not isinstance(row, Mapping):
            continue
        taxonomy = taxonomy_for_fact(row)
        tier_counts[str(taxonomy["tier"])] += 1
        classified = OrderedDict(
            [
                ("index", index),
                ("phase_id", row.get("phase_id")),
                ("source_phase", row.get("source_phase")),
                ("fact_type", _norm(row.get("fact_type")) or "unspecified_fact"),
                ("entity_type", _norm(row.get("entity_type")) or "fact_entity"),
                ("entity_id", _entity_name(row)),
                ("metric_name", _norm(row.get("metric_name"))),
                ("window_days", _window(row)),
                ("metric_value", _round(_metric_value(row))),
                ("evidence_count", _raw_evidence_count(row)),
                ("confidence_label", _text(row.get("confidence_label") or row.get("confidence") or _payload(row).get("confidence_label")).upper() or "LOW"),
                ("taxonomy", taxonomy),
                ("categories", _categories(row)),
            ]
        )
        if taxonomy["tier"] == "C":
            diagnostics.append(classified)
        else:
            ecosystem.append(classified)
    return ecosystem, diagnostics, OrderedDict((tier, tier_counts.get(tier, 0)) for tier in ("A", "B", "C"))


def _score(category: str, *, taxonomy_weight: float, values: Sequence[float], evidence_count: int, window_coverage: int, phase_coverage: int, recurrence_count: int, persistence_count: int, confidence_points: float) -> float:
    normalized_values = [abs(value) if category == "drift" else max(0.0, value) for value in values]
    avg_value = sum(normalized_values) / len(normalized_values) if normalized_values else 0.0
    max_value = max(normalized_values) if normalized_values else 0.0
    value_component = min(1.0, (0.6 * avg_value) + (0.4 * max_value))
    support_component = min(1.0, (min(evidence_count, 8) * 0.08) + (min(window_coverage, 5) * 0.12) + (min(phase_coverage, 4) * 0.10) + (min(recurrence_count, 5) * 0.06) + (min(persistence_count, 5) * 0.06))
    confidence_component = min(1.0, confidence_points)
    raw = taxonomy_weight * ((0.5 * value_component) + (0.3 * support_component) + (0.2 * confidence_component))
    return _round(raw) or 0.0


def _aggregate(facts: Sequence[Mapping[str, Any]], *, category: str, top_n: int) -> list[OrderedDict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for row in facts:
        if category not in set(row.get("categories") or []):
            continue
        entity_type = _norm(row.get("entity_type") or "fact_entity")
        name = _norm(row.get("entity_id") or "unknown")
        key = (entity_type, name)
        item = buckets.setdefault(
            key,
            {
                "entity_type": entity_type,
                "name": name,
                "values": [],
                "windows": set(),
                "phases": set(),
                "fact_types": Counter(),
                "metrics": Counter(),
                "evidence_rows": 0,
                "evidence_count": 0,
                "taxonomy_weights": [],
                "tiers": Counter(),
                "confidence_points": [],
                "supporting_evidence": [],
            },
        )
        value = _number(row.get("metric_value"))
        if value is not None:
            item["values"].append(float(value))
        if row.get("window_days") not in (None, ""):
            item["windows"].add(str(row.get("window_days")))
        phase = row.get("source_phase") or row.get("phase_id")
        if phase:
            item["phases"].add(str(phase))
        fact_type = _norm(row.get("fact_type")) or "unspecified_fact"
        metric_name = _norm(row.get("metric_name")) or "unspecified_metric"
        item["fact_types"][fact_type] += 1
        item["metrics"][metric_name] += 1
        item["evidence_rows"] += 1
        item["evidence_count"] += int(row.get("evidence_count") or 1)
        taxonomy = row.get("taxonomy") if isinstance(row.get("taxonomy"), Mapping) else {}
        item["taxonomy_weights"].append(float(taxonomy.get("weight") or TIER_B_WEIGHT))
        item["tiers"][_text(taxonomy.get("tier") or "B")] += 1
        item["confidence_points"].append(_confidence_points(row.get("confidence_label")))
        item["supporting_evidence"].append(f"{phase}:{fact_type}:{metric_name}:{row.get('window_days')}")
    rows: list[OrderedDict[str, Any]] = []
    score_key = SCORE_KEYS[category]
    for item in buckets.values():
        evidence_count = int(item["evidence_count"])
        evidence_rows = int(item["evidence_rows"])
        window_coverage = len(item["windows"])
        phase_coverage = len(item["phases"])
        recurrence_count = max(0, evidence_rows - 1)
        persistence_count = window_coverage if category == "persistence" else len([fact for fact in item["fact_types"] if "persistence" in fact])
        avg_weight = sum(item["taxonomy_weights"]) / len(item["taxonomy_weights"]) if item["taxonomy_weights"] else TIER_B_WEIGHT
        avg_confidence = sum(item["confidence_points"]) / len(item["confidence_points"]) if item["confidence_points"] else 0.4
        score = _score(
            category,
            taxonomy_weight=avg_weight,
            values=item["values"],
            evidence_count=evidence_count,
            window_coverage=window_coverage,
            phase_coverage=phase_coverage,
            recurrence_count=recurrence_count,
            persistence_count=persistence_count,
            confidence_points=avg_confidence,
        )
        rows.append(
            OrderedDict(
                [
                    ("entity_type", item["entity_type"]),
                    ("name", item["name"]),
                    (score_key, score),
                    ("taxonomy_tier", sorted(item["tiers"].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]),
                    ("taxonomy_weight", _round(avg_weight)),
                    ("confidence_label", _confidence_label(evidence_count, window_coverage, phase_coverage, recurrence_count, avg_confidence)),
                    ("evidence_count", evidence_count),
                    ("evidence_rows", evidence_rows),
                    ("window_coverage", window_coverage),
                    ("phase_coverage", phase_coverage),
                    ("recurrence_count", recurrence_count),
                    ("persistence_count", persistence_count),
                    ("average_metric_value", _round(sum(item["values"]) / len(item["values"])) if item["values"] else None),
                    ("max_metric_value", _round(max(item["values"])) if item["values"] else None),
                    ("dominant_fact_types", [name for name, _ in sorted(item["fact_types"].items(), key=lambda kv: (-kv[1], kv[0]))[:3]]),
                    ("dominant_metrics", [name for name, _ in sorted(item["metrics"].items(), key=lambda kv: (-kv[1], kv[0]))[:3]]),
                    ("supporting_windows", sorted(item["windows"], key=str)),
                    ("supporting_phases", sorted(item["phases"], key=str)),
                    ("supporting_evidence", sorted(item["supporting_evidence"])[:5]),
                ]
            )
        )
    return sorted(rows, key=lambda r: (-(r.get(score_key) or 0), -(r.get("taxonomy_weight") or 0), -r["window_coverage"], -r["recurrence_count"], -r["evidence_count"], r["entity_type"], r["name"]))[: _bounded_top_n(top_n)]


def _suppressed_diagnostics(diagnostics: Sequence[Mapping[str, Any]], top_n: int) -> list[OrderedDict[str, Any]]:
    buckets: Counter[tuple[str, str, str]] = Counter()
    for row in diagnostics:
        buckets[(_norm(row.get("fact_type")), _norm(row.get("metric_name")), _norm(row.get("entity_type")))] += 1
    return [
        OrderedDict(
            [
                ("fact_type", fact_type),
                ("metric_name", metric_name),
                ("entity_type", entity_type),
                ("taxonomy_tier", "C"),
                ("taxonomy_weight", TIER_C_WEIGHT),
                ("suppressed_count", count),
                ("reason", "Tier C operational telemetry is excluded from executive intelligence when Tier A/B ecosystem facts exist"),
            ]
        )
        for (fact_type, metric_name, entity_type), count in sorted(buckets.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1], kv[0][2]))[: _bounded_top_n(top_n)]
    ]


def _executive_summary(findings: Mapping[str, Sequence[Mapping[str, Any]]], has_tier_a: bool) -> list[str]:
    if not has_tier_a:
        return ["No Tier A ecosystem intelligence facts were available; executive intelligence is limited and no ecosystem claims are fabricated."]
    templates = [
        ("highest_ranked_ecosystem_hubs", "Ecosystem hub", "hub_score"),
        ("strongest_structural_anchors", "Structural anchor", "anchor_score"),
        ("replay_concentration_leaders", "Replay concentration leader", "replay_score"),
        ("cross_window_persistence_leaders", "Cross-window persistence leader", "persistence_score"),
        ("fragility_sources", "Fragility source", "fragility_score"),
        ("drift_morphology_change_leaders", "Drift/morphology change leader", "drift_score"),
        ("topology_findings", "Topology finding", "topology_score"),
    ]
    lines: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for section, label, score_key in templates:
        for row in findings.get(section) or []:
            if row.get("taxonomy_tier") != "A":
                continue
            key = (section, str(row.get("entity_type")), str(row.get("name")))
            if key in seen:
                continue
            seen.add(key)
            lines.append(
                f"{label}: {row.get('entity_type')} {row.get('name')} scored {row.get(score_key)} with Tier {row.get('taxonomy_tier')} weight {row.get('taxonomy_weight')}, {row.get('evidence_count')} evidence units, {row.get('window_coverage')} windows, and {row.get('confidence_label')} confidence."
            )
            if len(lines) >= 10:
                return lines
    return lines[:10]


def _load_local_facts(path: str | Path | None) -> tuple[list[Mapping[str, Any]], OrderedDict[str, Any]]:
    if not path:
        return [], OrderedDict([("path", None), ("status", "not_requested")])
    fact_path = Path(path)
    if not fact_path.exists():
        return [], OrderedDict([("path", fact_path.as_posix()), ("status", "missing")])
    payload = json.loads(fact_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)], OrderedDict([("path", fact_path.as_posix()), ("status", "loaded"), ("row_count", len(payload))])
    if isinstance(payload, Mapping) and isinstance(payload.get("expanded_facts"), list):
        rows = payload["expanded_facts"]
        return [row for row in rows if isinstance(row, Mapping)], OrderedDict([("path", fact_path.as_posix()), ("status", "loaded"), ("row_count", len(rows))])
    raise ValueError("local facts input must be a JSON list or an object with expanded_facts")


def build_taxonomy_weighted_intelligence(*, observation_facts: Iterable[Mapping[str, Any]] | None = None, local_facts_path: str | Path | None = None, top_n: int = DEFAULT_TOP_N, max_fact_rows: int = MAX_FACT_ROWS) -> OrderedDict[str, Any]:
    supplied = [row for row in (observation_facts or []) if isinstance(row, Mapping)]
    loaded_rows, input_status = _load_local_facts(local_facts_path)
    all_rows = (supplied + loaded_rows)[: max(0, min(int(max_fact_rows), MAX_FACT_ROWS))]
    ecosystem_facts, diagnostics, tier_counts = _classify_facts(all_rows, max_fact_rows)
    has_tier_a = tier_counts.get("A", 0) > 0
    limit = _bounded_top_n(top_n)
    findings: OrderedDict[str, Any] = OrderedDict(
        [
            ("executive_summary", []),
            ("highest_ranked_ecosystem_hubs", _aggregate(ecosystem_facts, category="hubs", top_n=limit)),
            ("strongest_structural_anchors", _aggregate(ecosystem_facts, category="anchors", top_n=limit)),
            ("replay_concentration_leaders", _aggregate(ecosystem_facts, category="replay", top_n=limit)),
            ("cross_window_persistence_leaders", _aggregate(ecosystem_facts, category="persistence", top_n=limit)),
            ("fragility_sources", _aggregate(ecosystem_facts, category="fragility", top_n=limit)),
            ("drift_morphology_change_leaders", _aggregate(ecosystem_facts, category="drift", top_n=limit)),
            ("topology_findings", _aggregate(ecosystem_facts, category="topology", top_n=limit)),
            ("suppressed_operational_diagnostics", _suppressed_diagnostics(diagnostics, limit) if has_tier_a else []),
        ]
    )
    findings["executive_summary"] = _executive_summary(findings, has_tier_a)
    limitations = [
        "Analysis is deterministic, local-only, and bounded to supplied HIST-FACT-1/observation fact rows; it does not collect live data or activate governed workflows.",
        "Taxonomy weights prioritize Tier A ecosystem intelligence over Tier B support context and suppress Tier C operational telemetry from executive intelligence whenever Tier A facts exist.",
    ]
    if not has_tier_a:
        limitations.append("No Tier A ecosystem intelligence facts were available, so executive findings are intentionally limited.")
    if diagnostics and has_tier_a:
        limitations.append("Tier C operational diagnostics were detected and reported only in the suppressed diagnostics section.")
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("phase_id", PHASE_ID),
            ("phase_name", PHASE_NAME),
            ("status", "ok" if has_tier_a else "limited"),
            ("top_n", limit),
            ("fact_rows_supplied", len(supplied)),
            ("fact_rows_loaded", len(loaded_rows)),
            ("fact_rows_considered", len(all_rows)),
            ("taxonomy_tier_counts", tier_counts),
            ("ecosystem_fact_rows", len(ecosystem_facts)),
            ("operational_diagnostic_rows_suppressed", len(diagnostics) if has_tier_a else 0),
            ("local_input_status", input_status),
            ("source_digest", _source_digest({"facts": all_rows, "input_status": input_status})),
            ("taxonomy_design", taxonomy_design()),
            ("governance_certification", governance_certification()),
            ("findings", findings),
            ("limitations", limitations),
        ]
    )


def taxonomy_design() -> OrderedDict[str, Any]:
    return OrderedDict(
        [
            ("tier_a", OrderedDict([("label", "Ecosystem Intelligence"), ("weight", TIER_A_WEIGHT), ("purpose", "drives executive findings"), ("fact_types", sorted(TIER_A_FACT_TYPES))])),
            ("tier_b", OrderedDict([("label", "Supporting Ecosystem Context"), ("weight", TIER_B_WEIGHT), ("purpose", "supports ecosystem sections below Tier A priority")])),
            ("tier_c", OrderedDict([("label", "Operational / Pipeline Telemetry"), ("weight", TIER_C_WEIGHT), ("purpose", "suppressed from executive findings when Tier A facts exist"), ("fact_types", sorted(TIER_C_FACT_TYPES)), ("metrics", sorted(OPERATIONAL_METRICS)), ("allowed_metric_entities", sorted(ALLOWED_ECOSYSTEM_METRIC_ENTITIES))])),
            ("ranking_inputs", ["taxonomy_weight", "confidence", "evidence_count", "window_coverage", "recurrence", "persistence", "entity_type", "entity_name"]),
        ]
    )


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# HIST-INTEL-2 Taxonomy-Weighted Intelligence Engine\n\n",
        "## Objective\nPrioritize ecosystem-significant facts over operational telemetry using deterministic fact taxonomy weights.\n\n",
        "## Governance certification\n",
    ]
    for key, value in (report.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {str(value).lower()}\n")
    lines.append("\n## Taxonomy design\n")
    for tier_key, tier in (report.get("taxonomy_design") or {}).items():
        if isinstance(tier, Mapping):
            lines.append(f"- {tier_key}: {tier.get('label')} weight={tier.get('weight')} purpose={tier.get('purpose')}\n")
    findings = report.get("findings") or {}
    lines.append("\n## Executive Summary\n")
    for item in findings.get("executive_summary") or []:
        lines.append(f"- {item}\n")
    sections = [
        ("Highest-Ranked Ecosystem Hubs", "highest_ranked_ecosystem_hubs", "hub_score"),
        ("Strongest Structural Anchors", "strongest_structural_anchors", "anchor_score"),
        ("Replay Concentration Leaders", "replay_concentration_leaders", "replay_score"),
        ("Cross-Window Persistence Leaders", "cross_window_persistence_leaders", "persistence_score"),
        ("Fragility Sources", "fragility_sources", "fragility_score"),
        ("Drift / Morphology Change Leaders", "drift_morphology_change_leaders", "drift_score"),
        ("Topology Findings", "topology_findings", "topology_score"),
    ]
    for title, key, score_key in sections:
        lines.append(f"\n## {title}\n")
        rows = findings.get(key) or []
        if not rows:
            lines.append("- No supported ecosystem findings from available fact rows.\n")
            continue
        for row in rows:
            lines.append(f"- {row.get('entity_type')} {row.get('name')}: {score_key}={row.get(score_key)} tier={row.get('taxonomy_tier')} weight={row.get('taxonomy_weight')} evidence_count={row.get('evidence_count')} window_coverage={row.get('window_coverage')} recurrence={row.get('recurrence_count')} confidence={row.get('confidence_label')}\n")
    lines.append("\n## Suppressed Operational Diagnostics\n")
    suppressed = findings.get("suppressed_operational_diagnostics") or []
    if not suppressed:
        lines.append("- No Tier C operational diagnostics were suppressed from executive intelligence.\n")
    for row in suppressed:
        lines.append(f"- {row.get('metric_name')} ({row.get('fact_type')}/{row.get('entity_type')}): suppressed_count={row.get('suppressed_count')} weight={row.get('taxonomy_weight')} reason={row.get('reason')}\n")
    lines.append("\n## Limitations\n")
    for item in report.get("limitations") or []:
        lines.append(f"- {item}\n")
    return "".join(lines)


def write_reports(report: Mapping[str, Any], *, json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH, markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH) -> OrderedDict[str, str]:
    json_path = Path(json_report_path)
    markdown_path = Path(markdown_report_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return OrderedDict([("json_report_path", json_path.as_posix()), ("markdown_report_path", markdown_path.as_posix())])


def run_hist_intel2(*, observation_facts: Iterable[Mapping[str, Any]] | None = None, local_facts_path: str | Path | None = DEFAULT_EXPANDED_FACTS_PATH, top_n: int = DEFAULT_TOP_N, json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH, markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH) -> OrderedDict[str, Any]:
    report = build_taxonomy_weighted_intelligence(observation_facts=observation_facts, local_facts_path=local_facts_path, top_n=top_n)
    paths = write_reports(report, json_report_path=json_report_path, markdown_report_path=markdown_report_path)
    report["output_paths"] = paths
    return report
