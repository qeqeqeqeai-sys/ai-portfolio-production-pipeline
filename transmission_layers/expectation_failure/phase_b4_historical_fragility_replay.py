"""Phase B4 deterministic historical expectation fragility replay interpretation."""

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
PHASE_ID = "B4"
PHASE_NAME = "Historical Expectation Fragility Replay Interpretation"
EXPLANATION_TEMPLATE_ID = "template_phase_b4_historical_replay_v1"
CLASSIFICATION_RULE_VERSION = "b4_rules_v1"
THRESHOLD_VERSION = "b4_thresholds_v1"
EXPLANATION_TEMPLATE_VERSION = "b4_templates_v1"
ARCH = ["deterministic_only", "replayable", "explainable", "bounded_labels", "bounded_scores", "immutable_input_safe", "additive_only", "fixed_interaction_rules", "fixed_label_precedence", "fixed_explanation_templates", "no_trading_logic", "no_backtesting"]


def _round_half_up(v: float) -> int:
    return int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _stable_checksum(v: object) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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
    return {f: _normalize_score(entity, f, flags) for f in SCORE_FIELDS}, sorted(set(flags))


def _extract_entities(snapshot):
    if isinstance(snapshot, list):
        return [deepcopy(e) for e in snapshot]
    if isinstance(snapshot, dict):
        for key in ("entities", "entity_replay_interpretations", "rows"):
            if isinstance(snapshot.get(key), list):
                return [deepcopy(e) for e in snapshot[key]]
    return []


def _base_metadata(inp, out):
    return {
        "phase_id": PHASE_ID, "phase_name": PHASE_NAME,
        "classification_rule_version": CLASSIFICATION_RULE_VERSION,
        "threshold_version": THRESHOLD_VERSION,
        "explanation_template_version": EXPLANATION_TEMPLATE_VERSION,
        "input_checksum": _stable_checksum(inp), "output_checksum": _stable_checksum(out),
        "deterministic_sort_order": "entity_id_or_ticker_or_name_asc",
        "tie_breaker_policy": "entity_id_then_ticker_then_entity_name",
        "missing_data_policy": "fallback_50",
        "clamping_policy": "clamp_0_100",
        "entity_matching_policy": "exact_match_precedence_entity_id_ticker_entity_name",
        "snapshot_comparison_policy": "deterministic_pairwise_replay",
        "architecture_constraints": ARCH,
    }


def _match_key(entity: dict):
    return str(entity.get("entity_id") or entity.get("ticker") or entity.get("entity_name") or "UNKNOWN")


def _index_by_field(entities, field, used_cur, used_pri, flags):
    pairs = []
    left = {}
    right = {}
    for i, e in enumerate(entities[0]):
        k = e.get(field)
        if k is not None and i not in used_cur:
            left.setdefault(str(k), []).append(i)
    for i, e in enumerate(entities[1]):
        k = e.get(field)
        if k is not None and i not in used_pri:
            right.setdefault(str(k), []).append(i)
    for k in sorted(set(left).intersection(right)):
        li = sorted(left[k], key=lambda x: _match_key(entities[0][x]))
        ri = sorted(right[k], key=lambda x: _match_key(entities[1][x]))
        if len(li) > 1 or len(ri) > 1:
            flags.add("duplicate_match_key")
        for a, b in zip(li, ri):
            used_cur.add(a); used_pri.add(b); pairs.append((a, b))
    return pairs


def _match_entities(current, prior):
    used_cur, used_pri = set(), set()
    flags = set()
    pairs = []
    for field in ("entity_id", "ticker", "entity_name"):
        pairs.extend(_index_by_field((current, prior), field, used_cur, used_pri, flags))
    new_idx = sorted(set(range(len(current))) - used_cur)
    miss_idx = sorted(set(range(len(prior))) - used_pri)
    return pairs, new_idx, miss_idx, sorted(flags)


def build_historical_snapshot_summary(snapshot, snapshot_label="current"):
    entities = _extract_entities(snapshot)
    norms = [_normalize_entity(e) for e in entities]
    flags = sorted({f for _, ff in norms for f in ff})
    if not entities:
        out = {"snapshot_label": snapshot_label, "snapshot_date": None, "entity_count": 0, "subsector_count": 0, "average_ai_expectation_failure_score": 50, "average_valuation_stretch_score": 50, "average_fundamental_support_score": 50, "average_narrative_saturation_score": 50, "average_certainty_fragility_score": 50, "average_structural_weakness_score": 50, "fragile_entity_count": 0, "resilient_entity_count": 0, "evidence_quality_flags": ["missing_snapshot_entities"]}
        out["replay_metadata"] = _base_metadata(snapshot, out)
        return out
    scores = [n[0] for n in norms]
    def avg(k): return _round_half_up(sum(s[k] for s in scores) / len(scores))
    dates = sorted({str(e.get("snapshot_date")) for e in entities if e.get("snapshot_date") is not None})
    fragile = 0; resilient = 0
    for e, s in zip(entities, scores):
        if s["ai_expectation_failure_score"] >= 70 or str(e.get("downside_asymmetry_label") or "") in {"EXTREME", "HIGH"}:
            fragile += 1
        if s["ai_expectation_failure_score"] <= 45 and s["fundamental_support_score"] >= 60:
            resilient += 1
    out = {"snapshot_label": snapshot_label, "snapshot_date": dates[0] if len(dates) == 1 else None, "entity_count": len(entities), "subsector_count": len({str(e.get('subsector') or 'UNKNOWN') for e in entities}), "average_ai_expectation_failure_score": avg("ai_expectation_failure_score"), "average_valuation_stretch_score": avg("valuation_stretch_score"), "average_fundamental_support_score": avg("fundamental_support_score"), "average_narrative_saturation_score": avg("narrative_saturation_score"), "average_certainty_fragility_score": avg("certainty_fragility_score"), "average_structural_weakness_score": avg("structural_weakness_score"), "fragile_entity_count": fragile, "resilient_entity_count": resilient, "evidence_quality_flags": flags}
    out["replay_metadata"] = _base_metadata(snapshot, out)
    return out


def build_fragility_change_delta(current_entity, prior_entity):
    if not current_entity or not prior_entity:
        return {"entity_id": (current_entity or prior_entity or {}).get("entity_id"), "direction": "INSUFFICIENT_REPLAY_CONTEXT", "evidence_quality_flags": ["missing_replay_counterpart"]}
    c, cf = _normalize_entity(current_entity); p, pf = _normalize_entity(prior_entity)
    d = {
        "ai_expectation_failure_delta": c["ai_expectation_failure_score"] - p["ai_expectation_failure_score"],
        "valuation_stretch_delta": c["valuation_stretch_score"] - p["valuation_stretch_score"],
        "fundamental_support_delta": p["fundamental_support_score"] - c["fundamental_support_score"],
        "narrative_saturation_delta": c["narrative_saturation_score"] - p["narrative_saturation_score"],
        "certainty_fragility_delta": c["certainty_fragility_score"] - p["certainty_fragility_score"],
        "structural_weakness_delta": c["structural_weakness_score"] - p["structural_weakness_score"],
    }
    comp = _round_half_up(sum(d.values()) / 6)
    direction = "FRAGILITY_DETERIORATED" if comp >= 12 else "FRAGILITY_IMPROVED" if comp <= -12 else "FRAGILITY_STABLE"
    out = {"entity_id": current_entity.get("entity_id") or prior_entity.get("entity_id"), "current_snapshot_date": current_entity.get("snapshot_date"), "prior_snapshot_date": prior_entity.get("snapshot_date"), **d, "composite_change_delta": comp, "direction": direction, "evidence_quality_flags": sorted(set(cf + pf))}
    return out


def build_fragility_change_label(delta):
    if delta is None: return "INSUFFICIENT_REPLAY_CONTEXT"
    if delta >= 30: return "SEVERE_FRAGILITY_DETERIORATION"
    if delta >= 20: return "HIGH_FRAGILITY_DETERIORATION"
    if delta >= 12: return "MODERATE_FRAGILITY_DETERIORATION"
    if delta <= -20: return "HIGH_FRAGILITY_IMPROVEMENT"
    if delta <= -12: return "MODERATE_FRAGILITY_IMPROVEMENT"
    return "STABLE_FRAGILITY_PROFILE"


def _driver_from_delta(delta_row, deterioration=True):
    mapping = [("valuation_stretch_delta", "valuation_stretch"), ("fundamental_support_delta", "fundamental_support"), ("narrative_saturation_delta", "narrative_saturation"), ("certainty_fragility_delta", "certainty_fragility"), ("structural_weakness_delta", "structural_weakness"), ("ai_expectation_failure_delta", "ai_expectation_failure")]
    vals = []
    for k, n in mapping:
        v = delta_row.get(k, 0)
        if (deterioration and v > 0) or ((not deterioration) and v < 0):
            vals.append((abs(v), n, k))
    if not vals:
        return ("mixed_deterioration" if deterioration else "mixed_improvement"), None
    vals = sorted(vals, key=lambda x: (-x[0], [m[1] for m in mapping].index(x[1])))
    p = vals[0][1] + ("_deterioration" if deterioration else "_improvement")
    s = vals[1][1] + ("_deterioration" if deterioration else "_improvement") if len(vals) > 1 else None
    return p, s


def build_historical_deterioration_interpretation(current_entity, prior_entity):
    d = build_fragility_change_delta(current_entity, prior_entity); label = build_fragility_change_label(d.get("composite_change_delta"))
    p, s = _driver_from_delta(d, True)
    return {"entity_id": d.get("entity_id"), "change_label": label, "deterioration_driver": p, "secondary_driver": s, "composite_change_delta": d.get("composite_change_delta"), "interpretation_summary": f"{current_entity.get('entity_name') or current_entity.get('ticker') or d.get('entity_id') or 'UNKNOWN'} is classified as {label} because its historical fragility delta is {d.get('composite_change_delta')}, driven primarily by {p}. This is a deterministic historical expectation-fragility replay interpretation, not a trading recommendation or backtest.", "evidence_quality_flags": d.get("evidence_quality_flags", [])}


def build_historical_improvement_interpretation(current_entity, prior_entity):
    d = build_fragility_change_delta(current_entity, prior_entity); label = build_fragility_change_label(d.get("composite_change_delta"))
    p, s = _driver_from_delta(d, False)
    return {"entity_id": d.get("entity_id"), "change_label": label, "improvement_driver": p, "secondary_driver": s, "composite_change_delta": d.get("composite_change_delta"), "interpretation_summary": f"{current_entity.get('entity_name') or current_entity.get('ticker') or d.get('entity_id') or 'UNKNOWN'} is classified as {label} because its historical fragility delta is {d.get('composite_change_delta')}, driven primarily by {p}. This is a deterministic historical expectation-fragility replay interpretation, not a trading recommendation or backtest.", "evidence_quality_flags": d.get("evidence_quality_flags", [])}


def build_historical_stability_interpretation(current_entity, prior_entity):
    d = build_fragility_change_delta(current_entity, prior_entity); c, _ = _normalize_entity(current_entity); p, _ = _normalize_entity(prior_entity)
    if d.get("direction") == "INSUFFICIENT_REPLAY_CONTEXT": st = "INSUFFICIENT_REPLAY_CONTEXT"
    elif c["ai_expectation_failure_score"] >= 70 and p["ai_expectation_failure_score"] >= 70: st = "PERSISTENT_HIGH_FRAGILITY"
    elif c["ai_expectation_failure_score"] <= 45 and p["ai_expectation_failure_score"] <= 45: st = "PERSISTENT_LOW_FRAGILITY"
    elif 45 <= c["ai_expectation_failure_score"] <= 70 and 45 <= p["ai_expectation_failure_score"] <= 70: st = "PERSISTENT_MODERATE_FRAGILITY"
    else: st = "MIXED_STABLE_FRAGILITY"
    return {"entity_id": d.get("entity_id"), "change_label": build_fragility_change_label(d.get("composite_change_delta")), "stability_label": st, "composite_change_delta": d.get("composite_change_delta"), "stable_driver_profile": "stable_within_threshold_band", "interpretation_summary": f"{current_entity.get('entity_name') or current_entity.get('ticker') or d.get('entity_id') or 'UNKNOWN'} is classified as {st} with historical fragility delta {d.get('composite_change_delta')}. This is a deterministic historical expectation-fragility replay interpretation, not a trading recommendation or backtest.", "evidence_quality_flags": d.get("evidence_quality_flags", [])}


def build_entity_replay_interpretation(current_entity, prior_entity, b2_context=None, b3_context=None):
    d = build_fragility_change_delta(current_entity, prior_entity)
    change_label = build_fragility_change_label(d.get("composite_change_delta"))
    if d.get("direction") == "FRAGILITY_DETERIORATED": interp = build_historical_deterioration_interpretation(current_entity, prior_entity); primary = interp["deterioration_driver"]
    elif d.get("direction") == "FRAGILITY_IMPROVED": interp = build_historical_improvement_interpretation(current_entity, prior_entity); primary = interp["improvement_driver"]
    else: interp = build_historical_stability_interpretation(current_entity, prior_entity); primary = interp.get("stable_driver_profile")
    out = {"entity_id": current_entity.get("entity_id") or prior_entity.get("entity_id"), "ticker": current_entity.get("ticker") or prior_entity.get("ticker"), "entity_name": current_entity.get("entity_name") or prior_entity.get("entity_name"), "current_snapshot_date": current_entity.get("snapshot_date"), "prior_snapshot_date": prior_entity.get("snapshot_date"), "change_label": change_label, "direction": d.get("direction"), "composite_change_delta": d.get("composite_change_delta"), "component_deltas": {k: v for k, v in d.items() if k.endswith("_delta") and k != "composite_change_delta"}, "primary_change_driver": primary, "secondary_change_driver": interp.get("secondary_driver"), "stability_label": interp.get("stability_label"), "b2_current_context_used": (b2_context or {}).get("current"), "b2_prior_context_used": (b2_context or {}).get("prior"), "b3_current_context_used": (b3_context or {}).get("current"), "b3_prior_context_used": (b3_context or {}).get("prior"), "evidence_quality_flags": sorted(set(d.get("evidence_quality_flags", []))), "classification_rule_id": "b4_entity_replay_v1", "explanation_template_id": EXPLANATION_TEMPLATE_ID, "interpretation_summary": interp.get("interpretation_summary")}
    out["replay_metadata"] = _base_metadata({"current": current_entity, "prior": prior_entity}, out)
    return out


def build_subsector_replay_interpretation(current_snapshot, prior_snapshot):
    current = sorted(_extract_entities(current_snapshot), key=_match_key); prior = sorted(_extract_entities(prior_snapshot), key=_match_key)
    pairs, new_idx, miss_idx, dup_flags = _match_entities(current, prior)
    by_sub = {}
    for ci, pi in pairs:
        c, p = current[ci], prior[pi]
        s = str(c.get("subsector") or p.get("subsector") or "UNKNOWN")
        by_sub.setdefault(s, {"d": [], "det": 0, "imp": 0, "st": 0})
        e = build_entity_replay_interpretation(c, p)
        by_sub[s]["d"].append(e)
        by_sub[s]["det"] += int(e["direction"] == "FRAGILITY_DETERIORATED")
        by_sub[s]["imp"] += int(e["direction"] == "FRAGILITY_IMPROVED")
        by_sub[s]["st"] += int(e["direction"] == "FRAGILITY_STABLE")
    out = []
    for s in sorted({str(e.get("subsector") or "UNKNOWN") for e in current + prior}):
        curc = sum(1 for e in current if str(e.get("subsector") or "UNKNOWN") == s); pric = sum(1 for e in prior if str(e.get("subsector") or "UNKNOWN") == s)
        rows = by_sub.get(s, {"d": [], "det": 0, "imp": 0, "st": 0})["d"]
        avg = _round_half_up(sum(r["composite_change_delta"] for r in rows) / len(rows)) if rows else 0
        label = "INSUFFICIENT_SUBSECTOR_REPLAY_CONTEXT" if not rows else "SUBSECTOR_ACCELERATING_FRAGILITY" if avg >= 20 else "SUBSECTOR_RISING_FRAGILITY" if avg >= 12 else "SUBSECTOR_IMPROVING_FRAGILITY" if avg <= -12 else "SUBSECTOR_STABLE_FRAGILITY"
        out.append({"subsector": s, "current_member_count": curc, "prior_member_count": pric, "average_composite_change_delta": avg, "subsector_replay_label": label, "deteriorating_entity_count": by_sub.get(s, {"det": 0})["det"], "improving_entity_count": by_sub.get(s, {"imp": 0})["imp"], "stable_entity_count": by_sub.get(s, {"st": 0})["st"], "new_entity_count": sum(1 for i in new_idx if str(current[i].get("subsector") or "UNKNOWN") == s), "missing_entity_count": sum(1 for i in miss_idx if str(prior[i].get("subsector") or "UNKNOWN") == s), "dominant_change_driver": (rows[0]["primary_change_driver"] if rows else None), "representative_entities": [r.get("entity_id") for r in rows[:3]], "evidence_quality_flags": dup_flags, "interpretation_summary": f"Subsector {s} is classified as {label} with average replay delta {avg}."})
    return sorted(out, key=lambda x: x["subsector"])


def build_universe_replay_interpretation(current_snapshot, prior_snapshot):
    current = sorted(_extract_entities(current_snapshot), key=_match_key); prior = sorted(_extract_entities(prior_snapshot), key=_match_key)
    pairs, new_idx, miss_idx, dup_flags = _match_entities(current, prior)
    if not pairs:
        return {"current_entity_count": len(current), "prior_entity_count": len(prior), "matched_entity_count": 0, "new_entity_count": len(new_idx), "missing_entity_count": len(miss_idx), "average_composite_change_delta": 0, "universe_replay_label": "INSUFFICIENT_UNIVERSE_REPLAY_CONTEXT", "deteriorating_entity_count": 0, "improving_entity_count": 0, "stable_entity_count": 0, "dominant_change_driver": None, "evidence_quality_flags": dup_flags, "interpretation_summary": "Insufficient replay matches for universe interpretation."}
    rows = [build_entity_replay_interpretation(current[ci], prior[pi]) for ci, pi in pairs]
    avg = _round_half_up(sum(r["composite_change_delta"] for r in rows) / len(rows))
    label = "UNIVERSE_ACCELERATING_EXPECTATION_FRAGILITY" if avg >= 20 else "UNIVERSE_RISING_EXPECTATION_FRAGILITY" if avg >= 12 else "UNIVERSE_EASING_EXPECTATION_FRAGILITY" if avg <= -12 else "UNIVERSE_STABLE_EXPECTATION_FRAGILITY"
    return {"current_entity_count": len(current), "prior_entity_count": len(prior), "matched_entity_count": len(pairs), "new_entity_count": len(new_idx), "missing_entity_count": len(miss_idx), "average_composite_change_delta": avg, "universe_replay_label": label, "deteriorating_entity_count": sum(1 for r in rows if r["direction"] == "FRAGILITY_DETERIORATED"), "improving_entity_count": sum(1 for r in rows if r["direction"] == "FRAGILITY_IMPROVED"), "stable_entity_count": sum(1 for r in rows if r["direction"] == "FRAGILITY_STABLE"), "dominant_change_driver": rows[0]["primary_change_driver"], "evidence_quality_flags": dup_flags, "interpretation_summary": f"Universe replay is {label} with average delta {avg}."}


def build_b4_evidence_chain(entity_replay_output, current_entity, prior_entity):
    return {"entity_id": entity_replay_output.get("entity_id"), "phase_id": PHASE_ID, "current_snapshot_reference": {"snapshot_date": current_entity.get("snapshot_date"), "entity_id": current_entity.get("entity_id")}, "prior_snapshot_reference": {"snapshot_date": prior_entity.get("snapshot_date"), "entity_id": prior_entity.get("entity_id")}, "change_label": entity_replay_output.get("change_label"), "composite_change_delta": entity_replay_output.get("composite_change_delta"), "component_deltas": entity_replay_output.get("component_deltas"), "primary_change_driver": entity_replay_output.get("primary_change_driver"), "evidence_quality_flags": entity_replay_output.get("evidence_quality_flags", []), "b2_context_reference": {"current": entity_replay_output.get("b2_current_context_used"), "prior": entity_replay_output.get("b2_prior_context_used")}, "b3_context_reference": {"current": entity_replay_output.get("b3_current_context_used"), "prior": entity_replay_output.get("b3_prior_context_used")}, "replay_trace": ["B4 replay label", "current snapshot scores", "prior snapshot scores", "component deltas", "B2 asymmetry evolution if available", "B3 benchmark-relative evolution if available", "evidence quality flags"]}


def build_phase_b4_historical_replay_report(current_snapshot, prior_snapshot, b2_current_outputs=None, b2_prior_outputs=None, b3_current_outputs=None, b3_prior_outputs=None, evidence_context=None):
    current = sorted(_extract_entities(current_snapshot), key=_match_key); prior = sorted(_extract_entities(prior_snapshot), key=_match_key)
    pairs, new_idx, miss_idx, _ = _match_entities(current, prior)
    b2_ctx = {"current": b2_current_outputs, "prior": b2_prior_outputs}
    b3_ctx = {"current": b3_current_outputs, "prior": b3_prior_outputs}
    entities = [build_entity_replay_interpretation(current[ci], prior[pi], b2_ctx, b3_ctx) for ci, pi in pairs]
    entities.extend({"entity_id": current[i].get("entity_id"), "change_label": "NEW_ENTITY_IN_CURRENT_SNAPSHOT", "direction": "INSUFFICIENT_REPLAY_CONTEXT", "evidence_quality_flags": ["NEW_ENTITY_IN_CURRENT_SNAPSHOT"]} for i in new_idx)
    entities.extend({"entity_id": prior[i].get("entity_id"), "change_label": "ENTITY_MISSING_FROM_CURRENT_SNAPSHOT", "direction": "INSUFFICIENT_REPLAY_CONTEXT", "evidence_quality_flags": ["ENTITY_MISSING_FROM_CURRENT_SNAPSHOT"]} for i in miss_idx)
    chains = [build_b4_evidence_chain(e, current[ci], prior[pi]) for e, (ci, pi) in zip([x for x in entities if x.get("component_deltas")], pairs)]
    uni = build_universe_replay_interpretation(current_snapshot, prior_snapshot)
    subs = build_subsector_replay_interpretation(current_snapshot, prior_snapshot)
    out = {"phase_id": PHASE_ID, "phase_name": PHASE_NAME, "current_snapshot_summary": build_historical_snapshot_summary(current_snapshot, "current"), "prior_snapshot_summary": build_historical_snapshot_summary(prior_snapshot, "prior"), "entity_replay_interpretations": sorted(entities, key=lambda e: str(e.get("entity_id") or "")), "subsector_replay_interpretations": subs, "universe_replay_interpretation": uni, "evidence_chains": chains}
    out["summary"] = {"current_entity_count": len(current), "prior_entity_count": len(prior), "matched_entity_count": len(pairs), "new_entity_count": len(new_idx), "missing_entity_count": len(miss_idx), "deteriorating_entity_count": sum(1 for e in entities if e.get("direction") == "FRAGILITY_DETERIORATED"), "improving_entity_count": sum(1 for e in entities if e.get("direction") == "FRAGILITY_IMPROVED"), "stable_entity_count": sum(1 for e in entities if e.get("direction") == "FRAGILITY_STABLE"), "persistent_high_fragility_count": sum(1 for e in entities if e.get("stability_label") == "PERSISTENT_HIGH_FRAGILITY"), "universe_replay_label": uni.get("universe_replay_label"), "dominant_replay_drivers": sorted({e.get("primary_change_driver") for e in entities if e.get("primary_change_driver")})}
    out["replay_metadata"] = _base_metadata({"current": current_snapshot, "prior": prior_snapshot}, out)
    out["architecture_constraints"] = ARCH
    return out
