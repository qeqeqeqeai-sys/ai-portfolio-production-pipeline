"""Phase B3 deterministic benchmark-relative expectation fragility interpretation."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Dict, Iterable, List, Tuple

SCORE_FIELDS: Tuple[str, ...] = (
    "ai_expectation_failure_score",
    "valuation_stretch_score",
    "fundamental_support_score",
    "narrative_saturation_score",
    "certainty_fragility_score",
    "structural_weakness_score",
)

EXPLANATION_TEMPLATE_ID = "template_phase_b3_benchmark_relative_v1"
CLASSIFICATION_RULE_VERSION = "b3_rules_v1"
THRESHOLD_VERSION = "b3_thresholds_v1"
EXPLANATION_TEMPLATE_VERSION = "b3_templates_v1"


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _stable_checksum(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_score(entity: dict, field: str, flags: List[str]) -> int:
    raw = entity.get(field)
    if raw is None:
        flags.append(f"missing_{field}")
        return 50
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        flags.append(f"invalid_{field}")
        return 50
    value = float(raw)
    if value < 0:
        flags.append(f"clamped_{field}")
        return 0
    if value > 100:
        flags.append(f"clamped_{field}")
        return 100
    return _round_half_up(value)


def _normalize_entity(entity: dict) -> Tuple[Dict[str, int], List[str]]:
    flags: List[str] = []
    scores = {f: _normalize_score(entity, f, flags) for f in SCORE_FIELDS}
    return scores, sorted(set(flags))


def build_benchmark_context_summary(entities, group_key=None):
    rows = [deepcopy(e) for e in entities]
    if not rows:
        return []
    groups: Dict[str, List[dict]] = {}
    if group_key:
        for row in rows:
            gid = str(row.get(group_key) or "UNKNOWN")
            groups.setdefault(gid, []).append(row)
    else:
        groups["UNIVERSE"] = rows

    out = []
    for idx, (gid, members) in enumerate(sorted(groups.items()), start=1):
        normalized = [_normalize_entity(m) for m in members]
        scores_only = [x[0] for x in normalized]
        flags = sorted({f for _, ff in normalized for f in ff})
        avg = {f"average_{k}": _round_half_up(sum(s[k] for s in scores_only) / len(scores_only)) for k in SCORE_FIELDS}
        span = max(s["ai_expectation_failure_score"] for s in scores_only) - min(s["ai_expectation_failure_score"] for s in scores_only)
        btype = "universe" if not group_key else ("subsector" if "subsector" in group_key else ("peer_group" if "peer" in group_key else "custom_benchmark"))
        summary = {
            "benchmark_id": gid,
            "benchmark_type": btype,
            "member_count": len(members),
            **avg,
            "dispersion_band": "wide" if span >= 35 else "moderate" if span >= 20 else "tight",
            "evidence_quality_flags": flags,
            "deterministic_sort_order": idx,
        }
        replay = {
            "phase_id": "B3",
            "phase_name": "Benchmark-Relative Expectation Fragility Interpretation",
            "classification_rule_version": CLASSIFICATION_RULE_VERSION,
            "threshold_version": THRESHOLD_VERSION,
            "explanation_template_version": EXPLANATION_TEMPLATE_VERSION,
            "deterministic_sort_order": "benchmark_id_asc",
            "tie_breaker_policy": "benchmark_id_then_entity_id",
            "missing_data_policy": "fallback_50",
            "clamping_policy": "clamp_0_100",
            "benchmark_context_policy": "derived_from_entities_when_missing",
            "architecture_constraints": ["deterministic_only", "bounded_labels", "replayable", "explainable", "immutable_input_safe", "additive_only", "no_trading_logic"],
        }
        replay["input_checksum"] = _stable_checksum(members)
        replay["output_checksum"] = _stable_checksum({k: v for k, v in summary.items() if k != "replay_metadata"})
        summary["replay_metadata"] = replay
        out.append(summary)
    return out


def build_relative_fragility_delta(entity, benchmark_summary):
    if not benchmark_summary:
        return {"entity_id": entity.get("entity_id"), "benchmark_id": None, "relative_fragility_direction": "INSUFFICIENT_BENCHMARK_CONTEXT", "evidence_quality_flags": ["missing_benchmark_context"]}
    scores, flags = _normalize_entity(entity)
    b = benchmark_summary
    deltas = {
        "ai_expectation_failure_delta": scores["ai_expectation_failure_score"] - b["average_ai_expectation_failure_score"],
        "valuation_stretch_delta": scores["valuation_stretch_score"] - b["average_valuation_stretch_score"],
        "fundamental_support_delta": b["average_fundamental_support_score"] - scores["fundamental_support_score"],
        "narrative_saturation_delta": scores["narrative_saturation_score"] - b["average_narrative_saturation_score"],
        "certainty_fragility_delta": scores["certainty_fragility_score"] - b["average_certainty_fragility_score"],
        "structural_weakness_delta": scores["structural_weakness_score"] - b["average_structural_weakness_score"],
    }
    fragility_delta = _round_half_up(sum(deltas.values()) / 6)
    if fragility_delta >= 15:
        direction = "MORE_FRAGILE_THAN_BENCHMARK"
    elif fragility_delta <= -15:
        direction = "LESS_FRAGILE_THAN_BENCHMARK"
    else:
        direction = "IN_LINE_WITH_BENCHMARK"
    return {"entity_id": entity.get("entity_id"), "benchmark_id": b.get("benchmark_id"), "fragility_delta": fragility_delta, **deltas, "relative_fragility_direction": direction, "evidence_quality_flags": flags}


def build_benchmark_relative_fragility_label(delta: int) -> str:
    if delta is None:
        return "INSUFFICIENT_BENCHMARK_CONTEXT"
    if delta >= 30:
        return "EXTREME_RELATIVE_FRAGILITY"
    if delta >= 20:
        return "HIGH_RELATIVE_FRAGILITY"
    if delta >= 10:
        return "MODERATE_RELATIVE_FRAGILITY"
    if delta <= -20:
        return "HIGH_RELATIVE_RESILIENCE"
    if delta <= -10:
        return "RELATIVE_RESILIENCE"
    return "IN_LINE_RELATIVE_FRAGILITY"


def _dominant_driver(delta_row: dict) -> Tuple[str, str]:
    ordered = [
        "valuation_stretch_delta",
        "fundamental_support_delta",
        "narrative_saturation_delta",
        "certainty_fragility_delta",
        "structural_weakness_delta",
        "ai_expectation_failure_delta",
    ]
    best = max(ordered, key=lambda k: (abs(delta_row.get(k, 0)), -ordered.index(k)))
    offsets = [k for k in ordered if delta_row.get(k, 0) < 0]
    return best, (offsets[0] if offsets else "mixed_relative_fragility")


def _relative_label(delta: int, prefix: str) -> str:
    if delta >= 25:
        return f"{prefix}_FRAGILE_OUTLIER"
    if delta >= 10:
        return f"{prefix}_ELEVATED_FRAGILITY"
    if delta <= -25:
        return f"{prefix}_RESILIENT_OUTLIER"
    if delta <= -10:
        return f"{prefix}_RELATIVE_RESILIENCE"
    return f"{prefix}_IN_LINE"


def build_peer_relative_fragility_interpretation(entity, peer_context):
    if not peer_context:
        return {"entity_id": entity.get("entity_id"), "peer_relative_label": "INSUFFICIENT_PEER_CONTEXT"}
    delta = build_relative_fragility_delta(entity, peer_context)
    dom, off = _dominant_driver(delta)
    label = _relative_label(delta["fragility_delta"], "PEER")
    summary = f"{entity.get('entity_name') or entity.get('ticker') or entity.get('entity_id') or 'UNKNOWN'} is classified as {label} versus {peer_context['benchmark_id']} because its fragility delta is {delta['fragility_delta']}, driven primarily by {dom}. This is a benchmark-relative expectation-fragility interpretation, not a trading recommendation."
    return {"entity_id": entity.get("entity_id"), "peer_group_id": peer_context.get("benchmark_id"), "peer_relative_label": label, "peer_fragility_delta": delta["fragility_delta"], "dominant_relative_driver": dom, "offsetting_relative_factor": off, "interpretation_summary": summary, "evidence_quality_flags": delta.get("evidence_quality_flags", [])}


def build_subsector_relative_fragility_interpretation(entity, subsector_context):
    if not subsector_context:
        return {"entity_id": entity.get("entity_id"), "subsector_relative_label": "INSUFFICIENT_SUBSECTOR_CONTEXT"}
    delta = build_relative_fragility_delta(entity, subsector_context)
    return {"entity_id": entity.get("entity_id"), "subsector_id": subsector_context.get("benchmark_id"), "subsector_relative_label": _relative_label(delta["fragility_delta"], "SUBSECTOR"), "subsector_fragility_delta": delta["fragility_delta"], "evidence_quality_flags": delta.get("evidence_quality_flags", [])}


def build_universe_relative_fragility_interpretation(entity, universe_context):
    if not universe_context:
        return {"entity_id": entity.get("entity_id"), "universe_relative_label": "INSUFFICIENT_UNIVERSE_CONTEXT"}
    delta = build_relative_fragility_delta(entity, universe_context)
    return {"entity_id": entity.get("entity_id"), "universe_id": universe_context.get("benchmark_id"), "universe_relative_label": _relative_label(delta["fragility_delta"], "UNIVERSE"), "universe_fragility_delta": delta["fragility_delta"], "evidence_quality_flags": delta.get("evidence_quality_flags", [])}


def build_benchmark_relative_resilience_interpretation(entity, benchmark_summary):
    delta = build_relative_fragility_delta(entity, benchmark_summary)
    if delta.get("relative_fragility_direction") == "INSUFFICIENT_BENCHMARK_CONTEXT":
        return {"entity_id": entity.get("entity_id"), "benchmark_relative_resilience_label": "INSUFFICIENT_BENCHMARK_CONTEXT"}
    d = delta["fragility_delta"]
    if d <= -20:
        label = "STRONG_BENCHMARK_RELATIVE_RESILIENCE"
    elif d <= -10:
        label = "MODERATE_BENCHMARK_RELATIVE_RESILIENCE"
    elif d < 10:
        label = "NEUTRAL_BENCHMARK_RELATIVE_RESILIENCE"
    elif d < 20:
        label = "WEAK_BENCHMARK_RELATIVE_RESILIENCE"
    else:
        label = "BENCHMARK_RELATIVE_FRAGILITY"
    return {"entity_id": entity.get("entity_id"), "benchmark_relative_resilience_label": label, "fragility_delta": d, "evidence_quality_flags": delta.get("evidence_quality_flags", [])}


def build_b3_evidence_chain(entity, benchmark_summary, peer_context=None, subsector_context=None, universe_context=None, b1_rankings=None, b2_asymmetry_outputs=None):
    safe = deepcopy(entity)
    scores, flags = _normalize_entity(safe)
    delta = build_relative_fragility_delta(safe, benchmark_summary)
    label = build_benchmark_relative_fragility_label(delta.get("fragility_delta"))
    dom, off = _dominant_driver(delta) if "fragility_delta" in delta else ("mixed_relative_fragility", "mixed_relative_fragility")
    peer = build_peer_relative_fragility_interpretation(safe, peer_context) if peer_context else None
    sub = build_subsector_relative_fragility_interpretation(safe, subsector_context) if subsector_context else None
    uni = build_universe_relative_fragility_interpretation(safe, universe_context) if universe_context else None
    summary = f"{safe.get('entity_name') or safe.get('ticker') or safe.get('entity_id') or 'UNKNOWN'} is classified as {label} versus {benchmark_summary.get('benchmark_id') if benchmark_summary else 'UNKNOWN'} because its fragility delta is {delta.get('fragility_delta')}, driven primarily by {dom}. This is a benchmark-relative expectation-fragility interpretation, not a trading recommendation."
    out = {
        "entity_id": safe.get("entity_id"), "entity_name": safe.get("entity_name") or safe.get("ticker"), "benchmark_id": benchmark_summary.get("benchmark_id") if benchmark_summary else None,
        "benchmark_type": benchmark_summary.get("benchmark_type") if benchmark_summary else None,
        "benchmark_relative_label": label, "relative_fragility_direction": delta.get("relative_fragility_direction"), "fragility_delta": delta.get("fragility_delta"),
        "component_deltas": {k: v for k, v in delta.items() if k.endswith("_delta")}, "dominant_relative_driver": dom, "offsetting_relative_factor": off,
        "peer_relative_label": peer.get("peer_relative_label") if peer else None,
        "subsector_relative_label": sub.get("subsector_relative_label") if sub else None,
        "universe_relative_label": uni.get("universe_relative_label") if uni else None,
        "b1_context_used": b1_rankings or [], "b2_context_used": b2_asymmetry_outputs or [], "normalized_scores": scores,
        "evidence_quality_flags": sorted(set(flags + delta.get("evidence_quality_flags", []))), "classification_rule_id": "b3_entity_chain_v1",
        "explanation_template_id": EXPLANATION_TEMPLATE_ID, "interpretation_summary": summary,
    }
    replay = {"phase_id": "B3", "phase_name": "Benchmark-Relative Expectation Fragility Interpretation", "classification_rule_version": CLASSIFICATION_RULE_VERSION, "threshold_version": THRESHOLD_VERSION, "explanation_template_version": EXPLANATION_TEMPLATE_VERSION, "deterministic_sort_order": "entity_id_or_ticker_asc", "tie_breaker_policy": "entity_id_then_ticker_then_name", "missing_data_policy": "fallback_50", "clamping_policy": "clamp_0_100", "benchmark_context_policy": "derived_from_entities_when_missing", "architecture_constraints": ["deterministic_only", "bounded_labels", "replayable", "explainable", "immutable_input_safe", "additive_only", "no_trading_logic"]}
    replay["input_checksum"] = _stable_checksum(safe)
    replay["output_checksum"] = _stable_checksum(out)
    out["replay_metadata"] = replay
    return out


def build_phase_b3_benchmark_relative_report(entities: Iterable[dict], benchmark_context=None, peer_groups=None, subsector_context=None, universe_context=None, b1_rankings=None, b2_asymmetry_outputs=None, evidence_context=None):
    ordered = sorted([deepcopy(e) for e in entities], key=lambda e: str(e.get("entity_id") or e.get("ticker") or e.get("entity_name") or ""))
    contexts = benchmark_context or build_benchmark_context_summary(ordered)
    universe_ctx = universe_context or (contexts[0] if contexts else None)
    by_id = {c["benchmark_id"]: c for c in contexts}
    chains = []
    peers, subs, unis, resilience = [], [], [], []
    for e in ordered:
        bench = by_id.get(str(e.get("benchmark_id") or ""), universe_ctx)
        peer_ctx = by_id.get(str(e.get("peer_group") or "")) if peer_groups is None else peer_groups.get(e.get("entity_id"))
        sub_ctx = by_id.get(str(e.get("subsector") or "")) if subsector_context is None else subsector_context.get(e.get("entity_id"))
        chain = build_b3_evidence_chain(e, bench, peer_context=peer_ctx, subsector_context=sub_ctx, universe_context=universe_ctx, b1_rankings=b1_rankings, b2_asymmetry_outputs=b2_asymmetry_outputs)
        chains.append(chain)
        peers.append(build_peer_relative_fragility_interpretation(e, peer_ctx))
        subs.append(build_subsector_relative_fragility_interpretation(e, sub_ctx))
        unis.append(build_universe_relative_fragility_interpretation(e, universe_ctx))
        resilience.append(build_benchmark_relative_resilience_interpretation(e, bench))
    high_frag = sum(c["benchmark_relative_label"] in {"EXTREME_RELATIVE_FRAGILITY", "HIGH_RELATIVE_FRAGILITY"} for c in chains)
    rel_res = sum(c["benchmark_relative_label"] in {"RELATIVE_RESILIENCE", "HIGH_RELATIVE_RESILIENCE"} for c in chains)
    insuff = sum("INSUFFICIENT" in str(c["benchmark_relative_label"]) for c in chains)
    drivers = {}
    for c in chains:
        drivers[c["dominant_relative_driver"]] = drivers.get(c["dominant_relative_driver"], 0) + 1
    summary = {"total_entities": len(ordered), "benchmark_context_count": len(contexts), "high_relative_fragility_count": high_frag, "relative_resilience_count": rel_res, "insufficient_context_count": insuff, "dominant_benchmark_fragility_drivers": [k for k, _ in sorted(drivers.items(), key=lambda kv: (-kv[1], kv[0]))]}
    report = {"phase_id": "B3", "phase_name": "Benchmark-Relative Expectation Fragility Interpretation", "benchmark_contexts": contexts, "entity_relative_interpretations": chains, "peer_relative_interpretations": peers, "subsector_relative_interpretations": subs, "universe_relative_interpretations": unis, "benchmark_relative_resilience_interpretations": resilience, "evidence_chains": chains, "summary": summary, "architecture_constraints": ["deterministic_only", "bounded_labels", "replayable", "explainable", "immutable_input_safe", "additive_only", "fixed_templates", "no_trading_logic"]}
    replay = {"phase_id": "B3", "phase_name": "Benchmark-Relative Expectation Fragility Interpretation", "classification_rule_version": CLASSIFICATION_RULE_VERSION, "threshold_version": THRESHOLD_VERSION, "explanation_template_version": EXPLANATION_TEMPLATE_VERSION, "deterministic_sort_order": "entity_id_or_ticker_asc", "tie_breaker_policy": "entity_id_then_ticker_then_name", "missing_data_policy": "fallback_50", "clamping_policy": "clamp_0_100", "benchmark_context_policy": "derived_from_entities_when_missing", "architecture_constraints": report["architecture_constraints"]}
    replay["input_checksum"] = _stable_checksum({"entities": ordered, "evidence_context": evidence_context or {}})
    replay["output_checksum"] = _stable_checksum({k: v for k, v in report.items() if k != "replay_metadata"})
    report["replay_metadata"] = replay
    return report
