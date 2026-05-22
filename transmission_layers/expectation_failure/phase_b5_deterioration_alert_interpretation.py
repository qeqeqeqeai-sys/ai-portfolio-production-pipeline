"""Phase B5 deterministic expectation deterioration alert interpretation layer."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Dict, List, Tuple

PHASE_ID = "B5"
PHASE_NAME = "Expectation Deterioration Alert Interpretation Layer"
CLASSIFICATION_RULE_VERSION = "b5_rules_v1"
THRESHOLD_VERSION = "b5_thresholds_v1"
EXPLANATION_TEMPLATE_VERSION = "b5_templates_v1"
EXPLANATION_TEMPLATE_ID = "template_phase_b5_deterioration_alert_v1"
ARCHITECTURE_CONSTRAINTS = [
    "deterministic_only", "replayable", "explainable", "bounded_labels", "bounded_scores", "immutable_input_safe",
    "additive_only", "fixed_interaction_rules", "fixed_label_precedence", "fixed_explanation_templates",
    "no_unrestricted_llm_reasoning", "no_optimization_loops", "no_adaptive_control", "no_trade_execution",
    "no_recommendations", "no_target_prices", "no_portfolio_allocation", "no_backtesting", "no_pnl_analysis",
    "no_predictive_timeseries", "no_autonomous_alert_dispatch", "no_notification_delivery"
]
SCORE_FIELDS: Tuple[str, ...] = (
    "ai_expectation_failure_score", "valuation_stretch_score", "fundamental_support_score",
    "narrative_saturation_score", "certainty_fragility_score", "structural_weakness_score",
)
TRIGGER_IDS = [
    "current_fragility_trigger", "asymmetry_trigger", "benchmark_relative_trigger", "historical_deterioration_trigger",
    "structural_weakness_trigger", "narrative_crowding_trigger", "certainty_fragility_trigger", "fundamental_support_weakness_trigger",
]


def _round_half_up(v: float) -> int:
    return int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _stable_checksum(v: object) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _base_metadata(inp: object, out: object) -> dict:
    return {
        "phase_id": PHASE_ID, "phase_name": PHASE_NAME,
        "classification_rule_version": CLASSIFICATION_RULE_VERSION,
        "threshold_version": THRESHOLD_VERSION,
        "explanation_template_version": EXPLANATION_TEMPLATE_VERSION,
        "input_checksum": _stable_checksum(inp), "output_checksum": _stable_checksum(out),
        "deterministic_sort_order": "entity_id_then_ticker_then_entity_name_asc",
        "tie_breaker_policy": "entity_id_then_ticker_then_entity_name",
        "missing_data_policy": "fallback_50_for_numeric_scores",
        "clamping_policy": "clamp_0_100_round_half_up",
        "alert_trigger_policy": "fixed_b5_trigger_thresholds_v1",
        "alert_escalation_policy": "fixed_b5_escalation_rules_v1",
        "architecture_constraints": ARCHITECTURE_CONSTRAINTS,
    }


def _norm_score(entity: dict, field: str, flags: List[str]) -> int:
    raw = entity.get(field)
    if raw is None:
        flags.append(f"missing_{field}")
        return 50
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        flags.append(f"invalid_{field}")
        return 50
    val = float(raw)
    if val < 0:
        flags.append(f"clamped_{field}")
        return 0
    if val > 100:
        flags.append(f"clamped_{field}")
        return 100
    return _round_half_up(val)


def _active(state: str) -> bool:
    return str(state).startswith("ACTIVE_")


def build_alert_trigger_evidence(entity, b2_context=None, b3_context=None, b4_context=None):
    entity = deepcopy(entity or {})
    b2_context = deepcopy(b2_context or {})
    b3_context = deepcopy(b3_context or {})
    b4_context = deepcopy(b4_context or {})
    flags: List[str] = []
    scores = {f: _norm_score(entity, f, flags) for f in SCORE_FIELDS}
    fragility_delta = b3_context.get("fragility_delta") if isinstance(b3_context.get("fragility_delta"), (int, float)) else 0
    change_delta = b4_context.get("composite_change_delta") if isinstance(b4_context.get("composite_change_delta"), (int, float)) else 0
    out = {
        "entity_id": entity.get("entity_id"),
        "current_fragility_trigger": scores["ai_expectation_failure_score"] >= 75,
        "asymmetry_trigger": str(b2_context.get("downside_asymmetry_label") or "") in {"EXTREME_DOWNSIDE_ASYMMETRY", "HIGH_DOWNSIDE_ASYMMETRY"},
        "benchmark_relative_trigger": str(b3_context.get("benchmark_relative_label") or "") in {"EXTREME_RELATIVE_FRAGILITY", "HIGH_RELATIVE_FRAGILITY"} or fragility_delta >= 20,
        "historical_deterioration_trigger": str(b4_context.get("change_label") or "") in {"SEVERE_FRAGILITY_DETERIORATION", "HIGH_FRAGILITY_DETERIORATION"} or change_delta >= 20,
        "structural_weakness_trigger": scores["structural_weakness_score"] >= 70,
        "narrative_crowding_trigger": scores["narrative_saturation_score"] >= 75,
        "certainty_fragility_trigger": scores["certainty_fragility_score"] >= 70,
        "fundamental_support_weakness_trigger": scores["fundamental_support_score"] <= 40,
        "evidence_quality_flags": sorted(set(flags)),
        "normalized_scores": {**scores, "fragility_delta": _round_half_up(fragility_delta), "composite_change_delta": _round_half_up(change_delta)},
    }
    out["trigger_ids"] = [k for k in TRIGGER_IDS if out.get(k)]
    out["trigger_count"] = len(out["trigger_ids"])
    return out


def build_alert_severity_label(trigger_evidence):
    te = deepcopy(trigger_evidence or {})
    ns = te.get("normalized_scores", {})
    contributions = []
    if te.get("current_fragility_trigger"): contributions.append(ns.get("ai_expectation_failure_score", 0))
    if te.get("asymmetry_trigger"): contributions.append(85)
    if te.get("benchmark_relative_trigger"): contributions.append(min(100, 50 + ns.get("fragility_delta", 0)))
    if te.get("historical_deterioration_trigger"): contributions.append(min(100, 50 + ns.get("composite_change_delta", 0)))
    if te.get("structural_weakness_trigger"): contributions.append(ns.get("structural_weakness_score", 0))
    if te.get("narrative_crowding_trigger"): contributions.append(ns.get("narrative_saturation_score", 0))
    if te.get("certainty_fragility_trigger"): contributions.append(ns.get("certainty_fragility_score", 0))
    if te.get("fundamental_support_weakness_trigger"): contributions.append(100 - ns.get("fundamental_support_score", 50))
    score = _round_half_up(sum(contributions) / len(contributions)) if contributions else 0
    tcount = int(te.get("trigger_count", 0))
    invalid_count = len([f for f in te.get("evidence_quality_flags", []) if f.startswith("invalid_")])
    if not contributions and invalid_count >= 3:
        label = "INSUFFICIENT_ALERT_EVIDENCE"
    elif score >= 85 and tcount >= 4:
        label = "CRITICAL_EXPECTATION_DETERIORATION_ALERT"
    elif score >= 70 and tcount >= 3:
        label = "HIGH_EXPECTATION_DETERIORATION_ALERT"
    elif score >= 50 and tcount >= 2:
        label = "ELEVATED_EXPECTATION_WATCHLIST_ALERT"
    elif tcount >= 1:
        label = "LOW_LEVEL_MONITORING_ALERT"
    else:
        label = "NO_ACTIVE_ALERT"
    return {"alert_severity_score": score, "alert_severity_label": label, "severity_driver": (te.get("trigger_ids") or [None])[0], "evidence_quality_flags": te.get("evidence_quality_flags", [])}


def build_deterioration_alert_state(entity, b2_context=None, b3_context=None, b4_context=None):
    te = build_alert_trigger_evidence(entity, b2_context=b2_context, b3_context=b3_context, b4_context=b4_context)
    sev = build_alert_severity_label(te)
    m = {
        "CRITICAL_EXPECTATION_DETERIORATION_ALERT": "ACTIVE_CRITICAL_DETERIORATION",
        "HIGH_EXPECTATION_DETERIORATION_ALERT": "ACTIVE_HIGH_DETERIORATION",
        "ELEVATED_EXPECTATION_WATCHLIST_ALERT": "ACTIVE_ELEVATED_WATCHLIST",
        "LOW_LEVEL_MONITORING_ALERT": "ACTIVE_LOW_LEVEL_MONITORING",
        "NO_ACTIVE_ALERT": "NO_ACTIVE_ALERT",
        "INSUFFICIENT_ALERT_EVIDENCE": "INSUFFICIENT_ALERT_CONTEXT",
    }
    return {
        "entity_id": (entity or {}).get("entity_id"), "alert_state": m[sev["alert_severity_label"]],
        "alert_severity_label": sev["alert_severity_label"], "alert_severity_score": sev["alert_severity_score"],
        "trigger_count": te["trigger_count"], "active_trigger_ids": te["trigger_ids"],
        "primary_alert_driver": (te["trigger_ids"][0] if te["trigger_ids"] else None),
        "secondary_alert_driver": (te["trigger_ids"][1] if len(te["trigger_ids"]) > 1 else None),
        "evidence_quality_flags": sorted(set(te["evidence_quality_flags"] + sev["evidence_quality_flags"])),
        "trigger_evidence": te,
    }


def build_alert_reason_classification(alert_state_output):
    o = alert_state_output or {}
    t = o.get("active_trigger_ids", [])
    if o.get("alert_state") == "INSUFFICIENT_ALERT_CONTEXT": return "INSUFFICIENT_ALERT_REASON_CONTEXT"
    if int(o.get("trigger_count", 0)) >= 3: return "MULTI_DRIVER_ALERT"
    precedence = [
        ("historical_deterioration_trigger", "HISTORICAL_DETERIORATION_BREACH"), ("benchmark_relative_trigger", "BENCHMARK_RELATIVE_BREACH"),
        ("asymmetry_trigger", "ASYMMETRY_BREACH"), ("current_fragility_trigger", "CURRENT_FRAGILITY_BREACH"),
        ("structural_weakness_trigger", "STRUCTURAL_WEAKNESS_BREACH"), ("narrative_crowding_trigger", "NARRATIVE_CROWDING_BREACH"),
        ("certainty_fragility_trigger", "CERTAINTY_FRAGILITY_BREACH"), ("fundamental_support_weakness_trigger", "FUNDAMENTAL_SUPPORT_WEAKNESS_BREACH"),
    ]
    for k, label in precedence:
        if k in t: return label
    return "NO_ALERT_REASON"


def build_alert_escalation_interpretation(current_alert_state, prior_alert_state=None):
    c = deepcopy(current_alert_state or {})
    p = deepcopy(prior_alert_state or {})
    cs, ps = int(c.get("alert_severity_score", 0)), int(p.get("alert_severity_score", 0))
    cur_active, pri_active = _active(c.get("alert_state")), _active(p.get("alert_state"))
    if not p and cur_active: label = "NEW_ALERT"
    elif pri_active and not cur_active: label = "CLEARED_ALERT"
    elif cs - ps >= 15: label = "ESCALATED_ALERT"
    elif ps - cs >= 15: label = "DE_ESCALATED_ALERT"
    elif c.get("alert_state") == p.get("alert_state") == "ACTIVE_CRITICAL_DETERIORATION": label = "PERSISTENT_CRITICAL_ALERT"
    elif c.get("alert_state") == p.get("alert_state") == "ACTIVE_HIGH_DETERIORATION": label = "PERSISTENT_HIGH_ALERT"
    elif c.get("alert_state") == p.get("alert_state") == "ACTIVE_ELEVATED_WATCHLIST": label = "PERSISTENT_WATCHLIST_ALERT"
    elif (not p) and (not cur_active): label = "NO_ALERT_STABLE"
    else: label = "NO_ALERT_STABLE"
    out = {"entity_id": c.get("entity_id"), "escalation_label": label, "prior_alert_state": p.get("alert_state"), "current_alert_state": c.get("alert_state"), "prior_alert_severity_score": ps, "current_alert_severity_score": cs, "severity_score_delta": cs - ps, "interpretation_summary": f"Alert escalation state is {label} under deterministic B5 escalation rules.", "evidence_quality_flags": sorted(set(c.get("evidence_quality_flags", []) + p.get("evidence_quality_flags", [])))}
    return out


def build_entity_alert_interpretation(entity, b2_context=None, b3_context=None, b4_context=None, prior_alert_state=None):
    e = deepcopy(entity or {})
    state = build_deterioration_alert_state(e, b2_context=b2_context, b3_context=b3_context, b4_context=b4_context)
    reason = build_alert_reason_classification(state)
    escalation = build_alert_escalation_interpretation(state, prior_alert_state=prior_alert_state)
    name = e.get("entity_name") or e.get("ticker") or e.get("entity_id") or "UNKNOWN"
    out = {
        "entity_id": e.get("entity_id"), "ticker": e.get("ticker"), "entity_name": e.get("entity_name"), "subsector": e.get("subsector"), "snapshot_date": e.get("snapshot_date"),
        "alert_state": state["alert_state"], "alert_severity_label": state["alert_severity_label"], "alert_severity_score": state["alert_severity_score"],
        "alert_reason_label": reason, "escalation_label": escalation["escalation_label"], "active_trigger_ids": state["active_trigger_ids"],
        "primary_alert_driver": state["primary_alert_driver"], "secondary_alert_driver": state["secondary_alert_driver"],
        "b2_context_used": deepcopy(b2_context), "b3_context_used": deepcopy(b3_context), "b4_context_used": deepcopy(b4_context),
        "prior_alert_state_used": deepcopy(prior_alert_state), "evidence_quality_flags": sorted(set(state["evidence_quality_flags"] + escalation["evidence_quality_flags"])),
        "classification_rule_id": "b5_entity_alert_interpretation_v1", "explanation_template_id": EXPLANATION_TEMPLATE_ID,
        "interpretation_summary": f"{name} is classified as {state['alert_state']} with {state['alert_severity_label']} because {state['trigger_count']} deterministic alert triggers are active, led by {state['primary_alert_driver']}. This is an expectation-deterioration alert interpretation, not an autonomous notification, recommendation, or execution instruction.",
    }
    out["replay_metadata"] = _base_metadata({"entity": e, "b2": b2_context, "b3": b3_context, "b4": b4_context, "prior_alert_state": prior_alert_state}, out)
    return out


def build_subsector_alert_interpretation(entity_alert_outputs):
    rows = sorted(deepcopy(entity_alert_outputs or []), key=lambda r: (str(r.get("subsector") or "UNKNOWN"), str(r.get("entity_id") or "")))
    by = {}
    for r in rows: by.setdefault(str(r.get("subsector") or "UNKNOWN"), []).append(r)
    out = []
    for s in sorted(by):
        g = by[s]; n = len(g); active = [r for r in g if _active(r.get("alert_state"))]
        crit = sum(r.get("alert_state") == "ACTIVE_CRITICAL_DETERIORATION" for r in g); high = sum(r.get("alert_state") == "ACTIVE_HIGH_DETERIORATION" for r in g); elev = sum(r.get("alert_state") == "ACTIVE_ELEVATED_WATCHLIST" for r in g)
        cleared = sum(r.get("escalation_label") == "CLEARED_ALERT" for r in g); new = sum(r.get("escalation_label") == "NEW_ALERT" for r in g)
        ratio = (len(active) / n) if n else 0
        if n == 0: label = "INSUFFICIENT_SUBSECTOR_ALERT_CONTEXT"
        elif crit >= 2 or (ratio >= 0.60 and crit > 0): label = "SUBSECTOR_CRITICAL_ALERT_CONCENTRATION"
        elif (crit + high) / n >= 0.50: label = "SUBSECTOR_HIGH_ALERT_CONCENTRATION"
        elif ratio >= 0.35: label = "SUBSECTOR_ELEVATED_WATCHLIST_CONCENTRATION"
        elif len(active) > 0: label = "SUBSECTOR_LOW_ALERT_ACTIVITY"
        else: label = "SUBSECTOR_NO_ACTIVE_ALERTS"
        reason_counts = {}
        for r in g: reason_counts[r.get("alert_reason_label")] = reason_counts.get(r.get("alert_reason_label"), 0) + 1
        dom = sorted(reason_counts.items(), key=lambda x: (-x[1], str(x[0])))[0][0] if reason_counts else "NO_ALERT_REASON"
        out.append({"subsector": s, "entity_count": n, "active_alert_count": len(active), "critical_alert_count": crit, "high_alert_count": high, "elevated_watchlist_count": elev, "cleared_alert_count": cleared, "new_alert_count": new, "subsector_alert_label": label, "dominant_alert_reason": dom, "representative_entities": [r.get("entity_id") for r in g[:3]], "evidence_quality_flags": sorted({f for r in g for f in r.get("evidence_quality_flags", [])}), "interpretation_summary": f"Subsector {s} is classified as {label} with {len(active)} active alerts out of {n} entities."})
    return out


def build_universe_alert_interpretation(entity_alert_outputs):
    rows = sorted(deepcopy(entity_alert_outputs or []), key=lambda r: str(r.get("entity_id") or ""))
    n = len(rows)
    active = [r for r in rows if _active(r.get("alert_state"))]
    crit = sum(r.get("alert_state") == "ACTIVE_CRITICAL_DETERIORATION" for r in rows); high = sum(r.get("alert_state") == "ACTIVE_HIGH_DETERIORATION" for r in rows); elev = sum(r.get("alert_state") == "ACTIVE_ELEVATED_WATCHLIST" for r in rows)
    cleared = sum(r.get("escalation_label") == "CLEARED_ALERT" for r in rows); new = sum(r.get("escalation_label") == "NEW_ALERT" for r in rows)
    ratio = (len(active) / n) if n else 0
    if n == 0: label = "INSUFFICIENT_UNIVERSE_ALERT_CONTEXT"
    elif crit >= 2 or (ratio >= 0.60 and crit > 0): label = "UNIVERSE_CRITICAL_DETERIORATION_ALERT_REGIME"
    elif (crit + high) / n >= 0.50: label = "UNIVERSE_HIGH_DETERIORATION_ALERT_REGIME"
    elif ratio >= 0.35: label = "UNIVERSE_ELEVATED_WATCHLIST_REGIME"
    elif len(active) > 0: label = "UNIVERSE_LOW_ALERT_ACTIVITY"
    else: label = "UNIVERSE_NO_ACTIVE_ALERTS"
    reason_counts = {}
    for r in rows: reason_counts[r.get("alert_reason_label")] = reason_counts.get(r.get("alert_reason_label"), 0) + 1
    dom = sorted(reason_counts.items(), key=lambda x: (-x[1], str(x[0])))[0][0] if reason_counts else "NO_ALERT_REASON"
    return {"total_entities": n, "active_alert_count": len(active), "critical_alert_count": crit, "high_alert_count": high, "elevated_watchlist_count": elev, "cleared_alert_count": cleared, "new_alert_count": new, "universe_alert_label": label, "dominant_alert_reason": dom, "alert_concentration_ratio": _round_half_up(ratio * 100) / 100, "representative_entities": [r.get("entity_id") for r in rows[:5]], "evidence_quality_flags": sorted({f for r in rows for f in r.get("evidence_quality_flags", [])}), "interpretation_summary": f"Universe is classified as {label} with {len(active)} active alerts across {n} entities."}


def build_b5_evidence_chain(entity_alert_output, entity, b2_context=None, b3_context=None, b4_context=None):
    return {"entity_id": entity_alert_output.get("entity_id"), "phase_id": PHASE_ID, "alert_state": entity_alert_output.get("alert_state"), "alert_severity_label": entity_alert_output.get("alert_severity_label"), "alert_reason_label": entity_alert_output.get("alert_reason_label"), "escalation_label": entity_alert_output.get("escalation_label"), "active_trigger_ids": entity_alert_output.get("active_trigger_ids"), "primary_alert_driver": entity_alert_output.get("primary_alert_driver"), "source_contexts": {"b4": deepcopy(b4_context), "b3": deepcopy(b3_context), "b2": deepcopy(b2_context), "current_scores": {f: (entity or {}).get(f) for f in SCORE_FIELDS}}, "evidence_quality_flags": entity_alert_output.get("evidence_quality_flags", []), "replay_trace": ["B5 alert state", "trigger evidence", "B4 historical deterioration context if available", "B3 benchmark-relative fragility context if available", "B2 asymmetry context if available", "current A7/A2-A6 score inputs", "evidence quality flags"]}


def build_phase_b5_alert_interpretation_report(current_entities, b2_outputs=None, b3_outputs=None, b4_outputs=None, prior_alert_states=None, evidence_context=None):
    entities = sorted([deepcopy(e) for e in (current_entities or [])], key=lambda x: (str(x.get("entity_id") or ""), str(x.get("ticker") or ""), str(x.get("entity_name") or "")))
    b2_map = {str(x.get("entity_id")): x for x in (b2_outputs or []) if x.get("entity_id") is not None}
    b3_map = {str(x.get("entity_id")): x for x in (b3_outputs or []) if x.get("entity_id") is not None}
    b4_map = {str(x.get("entity_id")): x for x in (b4_outputs or []) if x.get("entity_id") is not None}
    prior_map = {str(x.get("entity_id")): x for x in (prior_alert_states or []) if x.get("entity_id") is not None}
    entity_out, chains = [], []
    for e in entities:
        k = str(e.get("entity_id"))
        row = build_entity_alert_interpretation(e, b2_context=b2_map.get(k), b3_context=b3_map.get(k), b4_context=b4_map.get(k), prior_alert_state=prior_map.get(k))
        entity_out.append(row)
        chains.append(build_b5_evidence_chain(row, e, b2_context=b2_map.get(k), b3_context=b3_map.get(k), b4_context=b4_map.get(k)))
    sub = build_subsector_alert_interpretation(entity_out)
    uni = build_universe_alert_interpretation(entity_out)
    summary = {"total_entities": len(entity_out), "active_alert_count": sum(_active(r.get("alert_state")) for r in entity_out), "critical_alert_count": sum(r.get("alert_state") == "ACTIVE_CRITICAL_DETERIORATION" for r in entity_out), "high_alert_count": sum(r.get("alert_state") == "ACTIVE_HIGH_DETERIORATION" for r in entity_out), "elevated_watchlist_count": sum(r.get("alert_state") == "ACTIVE_ELEVATED_WATCHLIST" for r in entity_out), "low_level_monitoring_count": sum(r.get("alert_state") == "ACTIVE_LOW_LEVEL_MONITORING" for r in entity_out), "no_active_alert_count": sum(r.get("alert_state") == "NO_ACTIVE_ALERT" for r in entity_out), "new_alert_count": sum(r.get("escalation_label") == "NEW_ALERT" for r in entity_out), "escalated_alert_count": sum(r.get("escalation_label") == "ESCALATED_ALERT" for r in entity_out), "de_escalated_alert_count": sum(r.get("escalation_label") == "DE_ESCALATED_ALERT" for r in entity_out), "cleared_alert_count": sum(r.get("escalation_label") == "CLEARED_ALERT" for r in entity_out), "universe_alert_label": uni.get("universe_alert_label"), "dominant_alert_reasons": sorted({r.get("alert_reason_label") for r in entity_out})}
    out = {"phase_id": PHASE_ID, "phase_name": PHASE_NAME, "entity_alert_interpretations": entity_out, "subsector_alert_interpretations": sub, "universe_alert_interpretation": uni, "evidence_chains": chains, "summary": summary, "architecture_constraints": ARCHITECTURE_CONSTRAINTS}
    out["replay_metadata"] = _base_metadata({"current_entities": entities, "b2_outputs": b2_outputs, "b3_outputs": b3_outputs, "b4_outputs": b4_outputs, "prior_alert_states": prior_alert_states, "evidence_context": evidence_context}, out)
    return out
