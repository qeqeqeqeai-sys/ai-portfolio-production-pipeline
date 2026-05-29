from __future__ import annotations

import json
import math
from collections import Counter, OrderedDict, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from transmission_layers.history_long.hist_fact2_regime_evidence_expansion import (
    DEFAULT_EXPANDED_EVIDENCE_PATH as DEFAULT_FACT2_PATH,
    TRANSITION_RELEVANT_FACT_TYPES,
)
from transmission_layers.history_long.hist_intel2_taxonomy_weighted_intelligence import (
    CONFIDENCE_LABELS,
    DEFAULT_EXPANDED_FACTS_PATH as DEFAULT_FACT1_PATH,
    taxonomy_for_fact,
)

PHASE_ID = "HIST-INTEL-4"
PHASE_NAME = "HIST-INTEL-4_ecosystem_intelligence_synthesis"
SCHEMA_VERSION = "hist_intel4_v1"
DEFAULT_JSON_REPORT_PATH = "reports/hist_intel4_ecosystem_intelligence_synthesis.json"
DEFAULT_MARKDOWN_REPORT_PATH = "reports/hist_intel4_ecosystem_intelligence_synthesis.md"
DEFAULT_INTEL2_PATH = "reports/hist_intel2_taxonomy_weighted_intelligence.json"
DEFAULT_INTEL3_PATH = "reports/hist_intel3_narrative_evolution.json"
MAX_FACT_ROWS = 7500
MAX_EVIDENCE_ITEMS = 12

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

DOMAIN_TERMS: OrderedDict[str, tuple[str, ...]] = OrderedDict(
    [
        ("concentration", ("concentration", "hhi", "hub", "leader", "dominant", "share", "narrow")),
        ("replay", ("replay", "recurrence", "density", "saturation")),
        ("persistence", ("persistence", "persistent", "anchor", "durable", "cross_window", "decay")),
        ("topology", ("topology", "structural", "coherence", "fragmentation", "morphology", "stability")),
        ("fragility", ("fragility", "fragile", "instability", "weak", "failure", "pressure")),
        ("participation", ("participation", "breadth", "symbol_count", "effective_symbol")),
    ]
)

FORCE_LABELS: OrderedDict[str, str] = OrderedDict(
    [
        ("concentration", "concentration pressure"),
        ("replay", "replay persistence"),
        ("persistence", "persistence durability"),
        ("topology", "topology stability"),
        ("fragility", "fragility escalation"),
        ("participation", "participation expansion"),
    ]
)

IDENTITY_LABELS: OrderedDict[str, str] = OrderedDict(
    [
        ("concentration", "concentration-driven ecosystem"),
        ("replay", "replay-driven ecosystem"),
        ("persistence", "persistence-driven ecosystem"),
        ("topology", "topology-driven ecosystem"),
        ("fragility", "fragility-sensitive ecosystem"),
        ("participation", "participation-driven ecosystem"),
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
        for key in ("weighted_score", "score", "metric_value", "value", "share", "density", "ratio", "absolute_delta"):
            found = _number(value.get(key))
            if found is not None:
                return found
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _payload(row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = row.get("payload_jsonb") or row.get("payload") or {}
    return payload if isinstance(payload, Mapping) else {}


def _window(row: Mapping[str, Any]) -> int | None:
    payload = _payload(row)
    for key in ("window_days", "window_trading_days", "window", "lookback_days", "end_window_days"):
        value = row.get(key) if key in row else payload.get(key)
        number = _number(value)
        if number is not None:
            return int(number)
    return None


def _evidence_count(row: Mapping[str, Any]) -> int:
    payload = _payload(row)
    for key in ("evidence_count", "supporting_fact_count", "source_fact_count", "fact_count", "source_count"):
        number = _number(row.get(key) if key in row else payload.get(key))
        if number is not None:
            return max(1, int(number))
    return 1


def _confidence_points(label: Any) -> float:
    return {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4, "INSUFFICIENT": 0.1}.get(_text(label).upper(), 0.4)


def _confidence_label(score: float, fact_count: int, window_count: int) -> str:
    if fact_count <= 0:
        return "INSUFFICIENT"
    if score >= 1.25 and fact_count >= 5 and window_count >= 2:
        return "HIGH"
    if score >= 0.55 and fact_count >= 2:
        return "MEDIUM"
    return "LOW"


def _source_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _stable_id(parts: Sequence[Any]) -> str:
    return f"hist_intel4_{_source_digest(list(parts))}"


def _load_json(path: str | Path | None) -> tuple[Any, OrderedDict[str, Any]]:
    if not path:
        return None, OrderedDict([("path", None), ("status", "not_requested")])
    selected = Path(path)
    if not selected.exists():
        return None, OrderedDict([("path", selected.as_posix()), ("status", "missing")])
    payload = json.loads(selected.read_text(encoding="utf-8"))
    row_count = None
    if isinstance(payload, list):
        row_count = len(payload)
    elif isinstance(payload, Mapping):
        for key in ("expanded_facts", "expanded_regime_evidence", "facts"):
            if isinstance(payload.get(key), list):
                row_count = len(payload[key])
                break
    status = OrderedDict([("path", selected.as_posix()), ("status", "loaded")])
    if row_count is not None:
        status["row_count"] = row_count
    if isinstance(payload, Mapping) and payload.get("phase_id"):
        status["phase_id"] = payload.get("phase_id")
    return payload, status


def _extract_rows(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    if isinstance(payload, Mapping):
        for key in ("expanded_facts", "expanded_regime_evidence", "facts"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, Mapping)]
    return []


def _domain_from_text(text: str) -> str | None:
    haystack = _norm(text)
    for domain, terms in DOMAIN_TERMS.items():
        if any(term in haystack for term in terms):
            return domain
    return None


def _domain_for_fact(row: Mapping[str, Any]) -> str | None:
    payload = _payload(row)
    dimension = _norm(payload.get("dimension"))
    if dimension in DOMAIN_TERMS:
        return dimension
    parts = [row.get("fact_type"), row.get("entity_type"), row.get("entity_id"), row.get("metric_name"), row.get("source_phase")]
    for key in ("dimension", "section", "source_class", "narrative_type", "transition_label", "evidence_role"):
        parts.append(payload.get(key))
    return _domain_from_text(" ".join(_text(part) for part in parts if part is not None))


def _fact_metric_value(row: Mapping[str, Any]) -> float | None:
    value = _number(row.get("metric_value"))
    if value is not None:
        return value
    payload = _payload(row)
    for key in ("weighted_score", "score", "persistence_score", "stability_score", "fragility_score", "drift_score", "replay_density", "absolute_delta"):
        value = _number(payload.get(key))
        if value is not None:
            return value
    return None


def _fact_evidence(row: Mapping[str, Any], source: str, index: int) -> OrderedDict[str, Any] | None:
    domain = _domain_for_fact(row)
    if domain is None:
        return None
    confidence = _text(row.get("confidence_label") or row.get("confidence")).upper() or "LOW"
    if confidence not in CONFIDENCE_LABELS:
        confidence = "LOW"
    taxonomy = taxonomy_for_fact(row)
    window = _window(row)
    evidence_count = _evidence_count(row)
    metric_value = _fact_metric_value(row)
    metric_strength = min(1.0, abs(metric_value)) if metric_value is not None else 0.5
    score = float(taxonomy["weight"]) * _confidence_points(confidence) * (1.0 + math.log1p(evidence_count)) * (0.5 + metric_strength)
    if window is not None:
        score *= 1.1
    source_key = _text(row.get("fact_id")) or _stable_id([source, index, row.get("fact_type"), row.get("entity_id"), row.get("metric_name"), window])
    return OrderedDict(
        [
            ("evidence_id", _stable_id(["fact", source, source_key, domain])),
            ("source", source),
            ("domain", domain),
            ("fact_type", _norm(row.get("fact_type")) or "fact"),
            ("entity", _norm(row.get("entity_id")) or _norm(row.get("entity_type")) or "ecosystem"),
            ("window_days", window),
            ("confidence_label", confidence),
            ("supporting_fact_count", evidence_count),
            ("taxonomy_tier", taxonomy["tier"]),
            ("taxonomy_weight", taxonomy["weight"]),
            ("metric_value", _round(metric_value)),
            ("evidence_score", _round(score)),
        ]
    )


def _intel2_evidence(payload: Any) -> list[OrderedDict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    findings = payload.get("findings") or {}
    if not isinstance(findings, Mapping):
        return []
    section_domains = {
        "highest_ranked_ecosystem_hubs": "concentration",
        "strongest_structural_anchors": "persistence",
        "replay_concentration_leaders": "replay",
        "cross_window_persistence_leaders": "persistence",
        "fragility_sources": "fragility",
        "drift_morphology_change_leaders": "topology",
        "topology_findings": "topology",
    }
    rows: list[OrderedDict[str, Any]] = []
    for section, domain in section_domains.items():
        for index, row in enumerate(findings.get(section) or []):
            if not isinstance(row, Mapping):
                continue
            score = _number(row) or 0.5
            fact_count = _evidence_count(row)
            confidence = _text(row.get("confidence_label") or row.get("confidence")).upper() or _confidence_label(float(score), fact_count, len(row.get("windows") or row.get("supporting_windows") or []))
            if confidence not in CONFIDENCE_LABELS:
                confidence = "LOW"
            rows.append(
                OrderedDict(
                    [
                        ("evidence_id", _stable_id(["intel2", section, index, row.get("name") or row.get("entity") or row.get("entity_id") or "ecosystem"])),
                        ("source", "HIST-INTEL-2"),
                        ("domain", domain),
                        ("fact_type", section),
                        ("entity", _norm(row.get("name") or row.get("entity") or row.get("entity_id")) or "ecosystem"),
                        ("window_days", None),
                        ("confidence_label", confidence),
                        ("supporting_fact_count", fact_count),
                        ("taxonomy_tier", "A"),
                        ("taxonomy_weight", 1.0),
                        ("metric_value", _round(score)),
                        ("evidence_score", _round((1.0 + float(score)) * _confidence_points(confidence) * (1.0 + math.log1p(fact_count)))),
                    ]
                )
            )
    return rows


def _intel3_evidence(payload: Any) -> list[OrderedDict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    findings = payload.get("findings") or {}
    if not isinstance(findings, Mapping):
        return []
    rows: list[OrderedDict[str, Any]] = []
    section_domain_defaults = {
        "major_narrative_evolutions": None,
        "regime_transition_candidates": None,
        "stable_long_term_narratives": None,
        "persistence_evolution": "persistence",
        "replay_evolution": "replay",
        "concentration_evolution": "concentration",
        "topology_evolution": "topology",
        "fragility_evolution": "fragility",
    }
    for section, default_domain in section_domain_defaults.items():
        for index, row in enumerate(findings.get(section) or []):
            if not isinstance(row, Mapping):
                continue
            domain = default_domain or _domain_from_text(_text(row.get("narrative_type")) + " " + _text(row.get("transition_label")))
            if domain is None:
                continue
            fact_count = _evidence_count(row)
            windows = row.get("supporting_windows") if isinstance(row.get("supporting_windows"), list) else []
            confidence = _text(row.get("confidence_label") or row.get("confidence")).upper() or _confidence_label(0.8, fact_count, len(windows))
            if confidence not in CONFIDENCE_LABELS:
                confidence = "LOW"
            multiplier = 1.15 if section == "stable_long_term_narratives" else 1.0
            rows.append(
                OrderedDict(
                    [
                        ("evidence_id", _stable_id(["intel3", section, index, row.get("narrative_id") or domain])),
                        ("source", "HIST-INTEL-3"),
                        ("domain", domain),
                        ("fact_type", section),
                        ("entity", ",".join(sorted(_norm(item) for item in (row.get("supporting_entities") or [])[:3])) or "ecosystem"),
                        ("window_days", max(windows) if windows else None),
                        ("confidence_label", confidence),
                        ("supporting_fact_count", fact_count),
                        ("taxonomy_tier", "A"),
                        ("taxonomy_weight", 1.0),
                        ("metric_value", None),
                        ("evidence_score", _round(multiplier * _confidence_points(confidence) * (1.0 + math.log1p(fact_count)) * (1.0 + min(1.0, len(windows) / 3.0)))),
                    ]
                )
            )
    return rows


def _aggregate_domain_evidence(evidence: Iterable[Mapping[str, Any]]) -> OrderedDict[str, OrderedDict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in evidence:
        grouped[str(row["domain"])].append(row)
    aggregates: OrderedDict[str, OrderedDict[str, Any]] = OrderedDict()
    for domain in DOMAIN_TERMS:
        rows = grouped.get(domain, [])
        if not rows:
            continue
        windows = sorted({int(row["window_days"]) for row in rows if row.get("window_days") is not None})
        sources = sorted({str(row["source"]) for row in rows})
        confidence_counts = Counter(str(row["confidence_label"]) for row in rows)
        supporting_fact_count = sum(int(row.get("supporting_fact_count") or 0) for row in rows)
        recurrence = len(rows)
        total_score = sum(float(row.get("evidence_score") or 0.0) for row in rows)
        window_factor = 1.0 + min(1.0, len(windows) / 3.0)
        recurrence_factor = 1.0 + min(1.0, recurrence / 6.0)
        aggregate_score = total_score * window_factor * recurrence_factor
        confidence = _confidence_label(aggregate_score / max(1, recurrence), supporting_fact_count, len(windows))
        top = sorted(rows, key=lambda row: (-(float(row.get("evidence_score") or 0.0)), str(row.get("evidence_id"))))[:MAX_EVIDENCE_ITEMS]
        aggregates[domain] = OrderedDict(
            [
                ("domain", domain),
                ("force_label", FORCE_LABELS[domain]),
                ("aggregate_score", _round(aggregate_score)),
                ("confidence", confidence),
                ("supporting_fact_count", supporting_fact_count),
                ("window_coverage", windows),
                ("recurrence", recurrence),
                ("source_phases", sources),
                ("confidence_distribution", OrderedDict(sorted(confidence_counts.items()))),
                ("evidence_items", top),
            ]
        )
    return aggregates


def _rank_domains(aggregates: Mapping[str, Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    return [
        OrderedDict(row)
        for row in sorted(
            aggregates.values(),
            key=lambda row: (
                -(float(row.get("aggregate_score") or 0.0)),
                -int(row.get("supporting_fact_count") or 0),
                str(row.get("domain")),
            ),
        )
    ]


def _structural_identity(ranked: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    if not ranked:
        return OrderedDict([("identity", "mixed ecosystem"), ("primary_domain", None), ("confidence", "INSUFFICIENT"), ("statement", "Available local evidence is insufficient to assign a structural identity.")])
    first = ranked[0]
    second_score = float(ranked[1].get("aggregate_score") or 0.0) if len(ranked) > 1 else 0.0
    first_score = float(first.get("aggregate_score") or 0.0)
    if second_score and first_score / second_score < 1.15:
        identity = "mixed ecosystem"
        statement = f"Evidence is distributed across {first.get('force_label')} and {ranked[1].get('force_label')}, so no single structural force dominates the synthesis."
    else:
        identity = IDENTITY_LABELS.get(str(first.get("domain")), "mixed ecosystem")
        statement = f"The strongest accumulated evidence supports a {identity} with {first.get('supporting_fact_count')} supporting facts across {len(first.get('window_coverage') or [])} windows."
    return OrderedDict([("identity", identity), ("primary_domain", first.get("domain")), ("confidence", first.get("confidence")), ("statement", statement), ("supporting_evidence", first)])


def _stability_assessment(aggregates: Mapping[str, Mapping[str, Any]], intel3_payload: Any) -> OrderedDict[str, Any]:
    stable_score = sum(float((aggregates.get(domain) or {}).get("aggregate_score") or 0.0) for domain in ("persistence", "topology", "replay"))
    unstable_score = sum(float((aggregates.get(domain) or {}).get("aggregate_score") or 0.0) for domain in ("fragility", "concentration"))
    stable_narratives = 0
    if isinstance(intel3_payload, Mapping):
        stable_narratives = len(((intel3_payload.get("findings") or {}).get("stable_long_term_narratives") or []))
        stable_score += stable_narratives * 2.0
    total = stable_score + unstable_score
    ratio = stable_score / total if total else 0.0
    if total == 0:
        label = "mixed"
        confidence = "INSUFFICIENT"
    elif ratio >= 0.75 and stable_score >= 8:
        label = "highly stable"
        confidence = "HIGH" if stable_narratives and stable_score >= 16 else "MEDIUM"
    elif ratio >= 0.58:
        label = "stable"
        confidence = "MEDIUM"
    elif ratio >= 0.42:
        label = "mixed"
        confidence = "MEDIUM" if total >= 6 else "LOW"
    else:
        label = "unstable"
        confidence = "MEDIUM" if unstable_score >= 6 else "LOW"
    return OrderedDict([("classification", label), ("confidence", confidence), ("stable_evidence_score", _round(stable_score)), ("destabilizing_evidence_score", _round(unstable_score)), ("stable_narrative_count", stable_narratives)])


def _transition_readiness(fact2_rows: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    relevant: list[Mapping[str, Any]] = []
    for row in fact2_rows:
        fact_type = _norm(row.get("fact_type"))
        payload = _payload(row)
        role = _norm(payload.get("evidence_role"))
        if fact_type in TRANSITION_RELEVANT_FACT_TYPES or "transition" in fact_type or "transition" in role:
            relevant.append(row)
    pressure = sum((_number(row.get("metric_value")) or _number(_payload(row).get("absolute_delta")) or 0.0) * _confidence_points(row.get("confidence_label")) * (1.0 + math.log1p(_evidence_count(row))) for row in relevant)
    confirmations = sum(1 for row in relevant if "confirmation" in _norm(row.get("fact_type")))
    rejections = sum(1 for row in relevant if "rejection" in _norm(row.get("fact_type")))
    supporting = sum(_evidence_count(row) for row in relevant)
    if not relevant:
        label = "low transition readiness"
        confidence = "INSUFFICIENT"
    elif confirmations > 0 or pressure >= 4.0:
        label = "elevated transition readiness"
        confidence = "HIGH" if supporting >= 8 else "MEDIUM"
    elif pressure >= 1.0 and confirmations >= rejections:
        label = "moderate transition readiness"
        confidence = "MEDIUM"
    else:
        label = "low transition readiness"
        confidence = "MEDIUM" if relevant else "LOW"
    return OrderedDict([("classification", label), ("confidence", confidence), ("transition_evidence_count", len(relevant)), ("supporting_fact_count", supporting), ("pressure_score", _round(pressure)), ("confirmation_count", confirmations), ("rejection_count", rejections)])


def _narrative_continuity(intel3_payload: Any) -> OrderedDict[str, Any]:
    if not isinstance(intel3_payload, Mapping):
        return OrderedDict([("classification", "fragmented narratives"), ("confidence", "INSUFFICIENT"), ("stable_count", 0), ("evolving_count", 0), ("transition_candidate_count", 0)])
    findings = intel3_payload.get("findings") or {}
    stable = len(findings.get("stable_long_term_narratives") or []) if isinstance(findings, Mapping) else 0
    evolving = len(findings.get("major_narrative_evolutions") or []) if isinstance(findings, Mapping) else 0
    candidates = len(findings.get("regime_transition_candidates") or []) if isinstance(findings, Mapping) else 0
    diagnostics = intel3_payload.get("transition_diagnostics") or {}
    suppressed = int(_number(diagnostics.get("rejected_same_state_count")) or 0) if isinstance(diagnostics, Mapping) else 0
    if stable >= max(1, evolving + candidates):
        label = "stable narratives"
    elif evolving + candidates >= 2:
        label = "evolving narratives"
    else:
        label = "fragmented narratives"
    confidence = "HIGH" if stable + evolving + candidates + suppressed >= 5 else "MEDIUM" if stable + evolving + candidates else "LOW"
    return OrderedDict([("classification", label), ("confidence", confidence), ("stable_count", stable), ("evolving_count", evolving), ("transition_candidate_count", candidates), ("suppressed_same_state_count", suppressed)])


def _characterization(identity: Mapping[str, Any], forces: Sequence[Mapping[str, Any]], stability: Mapping[str, Any], transition: Mapping[str, Any], narrative: Mapping[str, Any]) -> OrderedDict[str, Any]:
    top_forces = [str(row.get("force_label")) for row in forces[:3]]
    force_text = ", ".join(top_forces) if top_forces else "insufficient recurring force evidence"
    statement = (
        f"The accumulated local evidence characterizes the ecosystem as {identity.get('identity')} shaped primarily by {force_text}. "
        f"Its stability profile is {stability.get('classification')}, narrative profile is {narrative.get('classification')}, "
        f"and transition profile is {transition.get('classification')}. This is a bounded evidence synthesis only."
    )
    confidence_values = [identity.get("confidence"), stability.get("confidence"), transition.get("confidence"), narrative.get("confidence")]
    if "INSUFFICIENT" in confidence_values:
        confidence = "LOW"
    elif confidence_values.count("HIGH") >= 2 and "LOW" not in confidence_values:
        confidence = "HIGH"
    elif "LOW" in confidence_values:
        confidence = "LOW"
    else:
        confidence = "MEDIUM"
    return OrderedDict([("characterization_id", _stable_id([identity.get("identity"), top_forces, stability.get("classification"), transition.get("classification"), narrative.get("classification")])), ("confidence", confidence), ("statement", statement)])


def build_ecosystem_intelligence_synthesis(
    *,
    fact1_path: str | Path | None = DEFAULT_FACT1_PATH,
    fact2_path: str | Path | None = DEFAULT_FACT2_PATH,
    intel2_path: str | Path | None = DEFAULT_INTEL2_PATH,
    intel3_path: str | Path | None = DEFAULT_INTEL3_PATH,
    observation_facts: Iterable[Mapping[str, Any]] | None = None,
    regime_evidence: Iterable[Mapping[str, Any]] | None = None,
    intel2_payload: Mapping[str, Any] | None = None,
    intel3_payload: Mapping[str, Any] | None = None,
    max_fact_rows: int = MAX_FACT_ROWS,
) -> OrderedDict[str, Any]:
    fact1_loaded, fact1_status = _load_json(fact1_path) if observation_facts is None else (None, OrderedDict([("path", None), ("status", "supplied")]))
    fact2_loaded, fact2_status = _load_json(fact2_path) if regime_evidence is None else (None, OrderedDict([("path", None), ("status", "supplied")]))
    intel2_loaded, intel2_status = _load_json(intel2_path) if intel2_payload is None else (intel2_payload, OrderedDict([("path", None), ("status", "supplied"), ("phase_id", "HIST-INTEL-2")]))
    intel3_loaded, intel3_status = _load_json(intel3_path) if intel3_payload is None else (intel3_payload, OrderedDict([("path", None), ("status", "supplied"), ("phase_id", "HIST-INTEL-3")]))

    fact1_rows = list(observation_facts or _extract_rows(fact1_loaded))[:MAX_FACT_ROWS]
    fact2_rows = list(regime_evidence or _extract_rows(fact2_loaded))[:MAX_FACT_ROWS]
    max_rows = max(0, min(int(max_fact_rows), MAX_FACT_ROWS))
    fact_evidence = []
    for source, rows in (("HIST-FACT-1", fact1_rows), ("HIST-FACT-2", fact2_rows)):
        for index, row in enumerate(rows[:max_rows]):
            item = _fact_evidence(row, source, index)
            if item is not None:
                fact_evidence.append(item)
    all_evidence = sorted(fact_evidence + _intel2_evidence(intel2_loaded) + _intel3_evidence(intel3_loaded), key=lambda row: str(row["evidence_id"]))
    aggregates = _aggregate_domain_evidence(all_evidence)
    ranked_forces = _rank_domains(aggregates)
    identity = _structural_identity(ranked_forces)
    stability = _stability_assessment(aggregates, intel3_loaded)
    transition = _transition_readiness(fact2_rows)
    narrative = _narrative_continuity(intel3_loaded)
    characterization = _characterization(identity, ranked_forces, stability, transition, narrative)
    source_digest = _source_digest({"fact1": fact1_rows, "fact2": fact2_rows, "intel2": intel2_loaded, "intel3": intel3_loaded})
    limitations = [
        "This is a synthesis layer over available local historical evidence; it does not generate new source facts or discover new transitions.",
        "The transition readiness assessment reports evidence-supported readiness only and does not describe future outcomes.",
        "Outputs are bounded and deterministic; missing local artifacts reduce confidence rather than being inferred.",
    ]
    if not all_evidence:
        limitations.append("No eligible local ecosystem evidence was available after taxonomy and domain filtering.")
    findings = OrderedDict(
        [
            ("executive_synthesis", characterization),
            ("structural_identity", identity),
            ("dominant_historical_forces", ranked_forces[:MAX_EVIDENCE_ITEMS]),
            ("stability_assessment", stability),
            ("transition_readiness_assessment", transition),
            ("narrative_continuity_assessment", narrative),
            ("ecosystem_characterization", characterization),
            ("evidence_summary", OrderedDict([("eligible_evidence_count", len(all_evidence)), ("fact1_rows", len(fact1_rows)), ("fact2_rows", len(fact2_rows)), ("domains_with_evidence", list(aggregates.keys())), ("total_supporting_fact_count", sum(int(row.get("supporting_fact_count") or 0) for row in all_evidence))])),
        ]
    )
    return OrderedDict(
        [
            ("schema_version", SCHEMA_VERSION),
            ("phase_id", PHASE_ID),
            ("phase_name", PHASE_NAME),
            ("status", "ok" if all_evidence else "limited"),
            ("synthesis_id", _stable_id([PHASE_ID, source_digest, characterization["characterization_id"]])),
            ("source_digest", source_digest),
            ("governance_certification", GOVERNANCE_CERTIFICATION.copy()),
            ("input_status", OrderedDict([("hist_fact1", fact1_status), ("hist_fact2", fact2_status), ("hist_intel2", intel2_status), ("hist_intel3", intel3_status)])),
            ("fact_rows_considered", len(fact1_rows) + len(fact2_rows)),
            ("evidence_rows_considered", len(all_evidence)),
            ("findings", findings),
            ("limitations", limitations),
        ]
    )


def render_markdown(report: Mapping[str, Any]) -> str:
    findings = report.get("findings") or {}
    lines = ["# HIST-INTEL-4 — Ecosystem Intelligence Synthesis\n\n"]
    lines.append("## Executive Synthesis\n")
    executive = findings.get("executive_synthesis") or {}
    lines.append(f"- {executive.get('statement', 'No supported executive synthesis from available local evidence.')}\n")
    lines.append(f"- Confidence: {executive.get('confidence', 'INSUFFICIENT')}\n")
    lines.append("\n## Structural Identity\n")
    identity = findings.get("structural_identity") or {}
    lines.append(f"- Identity: {identity.get('identity')}\n- Confidence: {identity.get('confidence')}\n- Evidence: {identity.get('statement')}\n")
    lines.append("\n## Dominant Historical Forces\n")
    for row in findings.get("dominant_historical_forces") or []:
        lines.append(f"- {row.get('force_label')}: score={row.get('aggregate_score')} confidence={row.get('confidence')} facts={row.get('supporting_fact_count')} windows={row.get('window_coverage')}\n")
    if not findings.get("dominant_historical_forces"):
        lines.append("- No supported dominant forces from available local evidence.\n")
    lines.append("\n## Stability Assessment\n")
    stability = findings.get("stability_assessment") or {}
    lines.append(f"- Classification: {stability.get('classification')}\n- Confidence: {stability.get('confidence')}\n- Stable evidence score: {stability.get('stable_evidence_score')}\n- Destabilizing evidence score: {stability.get('destabilizing_evidence_score')}\n")
    lines.append("\n## Transition Readiness Assessment\n")
    transition = findings.get("transition_readiness_assessment") or {}
    lines.append(f"- Classification: {transition.get('classification')}\n- Confidence: {transition.get('confidence')}\n- Transition evidence count: {transition.get('transition_evidence_count')}\n- Pressure score: {transition.get('pressure_score')}\n")
    lines.append("\n## Narrative Continuity Assessment\n")
    narrative = findings.get("narrative_continuity_assessment") or {}
    lines.append(f"- Classification: {narrative.get('classification')}\n- Confidence: {narrative.get('confidence')}\n- Stable narratives: {narrative.get('stable_count')}\n- Evolving narratives: {narrative.get('evolving_count')}\n")
    lines.append("\n## Ecosystem Characterization\n")
    characterization = findings.get("ecosystem_characterization") or {}
    lines.append(f"- {characterization.get('statement', 'No supported characterization.')}\n")
    lines.append("\n## Evidence Summary\n")
    for key, value in (findings.get("evidence_summary") or {}).items():
        lines.append(f"- {key}: {value}\n")
    lines.append("\n## Governance Certification\n")
    for key, value in (report.get("governance_certification") or {}).items():
        lines.append(f"- {key}: {str(value).lower()}\n")
    lines.append("\n## Limitations\n")
    for item in report.get("limitations") or []:
        lines.append(f"- {item}\n")
    return "".join(lines)


def write_reports(report: Mapping[str, Any], *, json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH, markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH) -> OrderedDict[str, str]:
    json_path = Path(json_report_path)
    md_path = Path(markdown_report_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return OrderedDict([("json_report_path", json_path.as_posix()), ("markdown_report_path", md_path.as_posix())])


def run_hist_intel4(
    *,
    fact1_path: str | Path | None = DEFAULT_FACT1_PATH,
    fact2_path: str | Path | None = DEFAULT_FACT2_PATH,
    intel2_path: str | Path | None = DEFAULT_INTEL2_PATH,
    intel3_path: str | Path | None = DEFAULT_INTEL3_PATH,
    json_report_path: str | Path = DEFAULT_JSON_REPORT_PATH,
    markdown_report_path: str | Path = DEFAULT_MARKDOWN_REPORT_PATH,
) -> OrderedDict[str, Any]:
    report = build_ecosystem_intelligence_synthesis(fact1_path=fact1_path, fact2_path=fact2_path, intel2_path=intel2_path, intel3_path=intel3_path)
    write_reports(report, json_report_path=json_report_path, markdown_report_path=markdown_report_path)
    return report
