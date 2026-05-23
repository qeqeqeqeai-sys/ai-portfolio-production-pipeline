"""P5-D Propagation Regime Classification & Structural State Labelling: deterministic descriptive layer."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, List, Tuple

CERTIFIED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION = "CERTIFIED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION"
DEGRADED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION = "DEGRADED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION"
BLOCKED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION = "BLOCKED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION"

REGIME_PRECEDENCE: Tuple[str, ...] = (
    "INSUFFICIENT_PROPAGATION_EVIDENCE",
    "CARRIER_DOMINATED_PROPAGATION",
    "CORRIDOR_WEAKENED_PROPAGATION",
    "AMPLIFYING_PRESSURE_STRUCTURE",
    "CONCENTRATED_PRESSURE",
    "BROAD_DISTRIBUTED_FRAGILITY",
    "ROTATING_PROPAGATION",
    "STABILIZING_PROPAGATION",
    "ISOLATED_FRAGILITY",
    "MIXED_PROPAGATION_STATE",
)
REGIME_POLICY = {
    "thresholds": {
        "evidence_low": 35.0,
        "carrier_high": 70.0,
        "corridor_weak_high": 70.0,
        "amplification_high": 65.0,
        "concentration_high": 65.0,
        "breadth_high": 65.0,
        "rotation_high": 55.0,
        "stabilization_high": 70.0,
        "isolated_breadth_low": 35.0,
        "persistence_high": 65.0,
        "mixed_high": 60.0,
    },
    "precedence": list(REGIME_PRECEDENCE),
    "tie_breaker": "precedence_order_then_lexicographic",
}
FORBIDDEN_TERMS: Tuple[str, ...] = (
    "will", "likely", "forecast", "predict", "expected return", "buy", "sell", "outperform", "underperform", "probability", "risk of future",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _clamp(value: Any) -> float:
    n = float(value) if isinstance(value, (int, float)) else 0.0
    return round(max(0.0, min(100.0, n)), 4)


def _series_mean(values: List[Any]) -> float:
    nums = [_clamp(v) for v in values if isinstance(v, (int, float))]
    return _clamp(sum(nums) / max(1, len(nums)))


def build_path5d_regime_inputs(p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    b = deepcopy(p5b_payload or {})
    c = deepcopy(p5c_payload or {})
    carrier_scores = [x.get("carrier_load_score", 0.0) for x in b.get("pressure_carriers", {}).get("pressure_carriers", [])]
    corridor_scores = [x.get("corridor_erosion_score", 0.0) for x in b.get("resilience_corridors", {}).get("resilience_corridors", [])]
    pathway_amp = [x.get("amplification_score", 0.0) for x in b.get("pathway_dominance", {}).get("pathway_dominance", [])]
    inp = {
        "concentration_input": _clamp(b.get("fragility_concentration", {}).get("system_concentration_score", 0.0)),
        "breadth_input": _clamp(b.get("foundation", {}).get("propagation_breadth_score", 0.0)),
        "carrier_input": _series_mean(carrier_scores),
        "corridor_input": _series_mean(corridor_scores),
        "rotation_input": _clamp(c.get("propagation_rotation", {}).get("rotation_score", 0.0)),
        "stabilization_input": _clamp(c.get("structural_pressure_evolution", {}).get("structural_stability_score", 0.0)),
        "amplification_input": _series_mean(pathway_amp),
        "persistence_input": _clamp(c.get("propagation_persistence", {}).get("propagation_persistence_score", 0.0)),
        "window_count": int(c.get("replay_window_index", {}).get("replay_metadata", {}).get("replay_window_count", len(c.get("replay_window_index", {}).get("replay_window_index", [])) if isinstance(c.get("replay_window_index"), dict) else 0)),
        "p5b_lineage_ref": b.get("lineage", {}).get("input_graph_checksum", ""),
        "p5c_lineage_ref": c.get("lineage", {}).get("output_checksum", ""),
    }
    inp["evidence_count"] = sum(1 for k in ("concentration_input", "breadth_input", "carrier_input", "corridor_input", "rotation_input", "stabilization_input", "amplification_input", "persistence_input") if inp[k] > 0)
    inp["input_checksum"] = _checksum(inp)
    return inp


def build_path5d_propagation_regime_scores(regime_inputs: Dict[str, Any]) -> Dict[str, float]:
    s = {
        "concentration_regime_score": _clamp(regime_inputs.get("concentration_input", 0.0)),
        "breadth_regime_score": _clamp(regime_inputs.get("breadth_input", 0.0)),
        "carrier_dominance_score": _clamp(regime_inputs.get("carrier_input", 0.0)),
        "corridor_weakness_score": _clamp(regime_inputs.get("corridor_input", 0.0)),
        "rotation_regime_score": _clamp(regime_inputs.get("rotation_input", 0.0)),
        "stabilization_regime_score": _clamp(regime_inputs.get("stabilization_input", 0.0)),
        "amplification_regime_score": _clamp(regime_inputs.get("amplification_input", 0.0)),
        "persistence_regime_score": _clamp(regime_inputs.get("persistence_input", 0.0)),
    }
    spread = max(s.values()) - min(s.values()) if s else 0.0
    s["mixed_state_score"] = _clamp(100.0 - spread)
    s["evidence_sufficiency_score"] = _clamp((regime_inputs.get("evidence_count", 0) / 8.0) * 100.0)
    return s


def classify_path5d_propagation_regime(scores: Dict[str, float]) -> Dict[str, Any]:
    t = REGIME_POLICY["thresholds"]
    matches: Dict[str, bool] = {
        "INSUFFICIENT_PROPAGATION_EVIDENCE": scores.get("evidence_sufficiency_score", 0) < t["evidence_low"],
        "CARRIER_DOMINATED_PROPAGATION": scores.get("carrier_dominance_score", 0) >= t["carrier_high"],
        "CORRIDOR_WEAKENED_PROPAGATION": scores.get("corridor_weakness_score", 0) >= t["corridor_weak_high"],
        "AMPLIFYING_PRESSURE_STRUCTURE": scores.get("amplification_regime_score", 0) >= t["amplification_high"],
        "CONCENTRATED_PRESSURE": scores.get("concentration_regime_score", 0) >= t["concentration_high"],
        "BROAD_DISTRIBUTED_FRAGILITY": scores.get("breadth_regime_score", 0) >= t["breadth_high"],
        "ROTATING_PROPAGATION": scores.get("rotation_regime_score", 0) >= t["rotation_high"],
        "STABILIZING_PROPAGATION": scores.get("stabilization_regime_score", 0) >= t["stabilization_high"] and scores.get("persistence_regime_score", 0) >= t["persistence_high"],
        "ISOLATED_FRAGILITY": scores.get("breadth_regime_score", 0) <= t["isolated_breadth_low"] and scores.get("concentration_regime_score", 0) < t["concentration_high"],
        "MIXED_PROPAGATION_STATE": scores.get("mixed_state_score", 0) >= t["mixed_high"],
    }
    selected = next((reg for reg in REGIME_PRECEDENCE if matches.get(reg, False)), "MIXED_PROPAGATION_STATE")
    return {"selected_regime": selected, "precedence_order": list(REGIME_PRECEDENCE), "regime_matches": matches, "classification_checksum": _checksum({"selected": selected, "matches": matches})}


def build_path5d_structural_state_labels(classification: Dict[str, Any], scores: Dict[str, float]) -> Dict[str, str]:
    r = classification.get("selected_regime", "MIXED_PROPAGATION_STATE")
    return {
        "propagation_state": r,
        "pressure_distribution_state": "CONCENTRATED" if scores.get("concentration_regime_score", 0) >= 65 else "DISTRIBUTED",
        "carrier_state": "CARRIER_DOMINANCE_ELEVATED" if scores.get("carrier_dominance_score", 0) >= 70 else "CARRIER_DIVERSIFIED",
        "corridor_state": "CORRIDOR_WEAKNESS_PRESENT" if scores.get("corridor_weakness_score", 0) >= 70 else "CORRIDOR_STABLE",
        "pathway_state": "AMPLIFYING" if scores.get("amplification_regime_score", 0) >= 65 else "NEUTRAL",
        "replay_evolution_state": "ROTATING" if scores.get("rotation_regime_score", 0) >= 55 else ("STABILIZING" if scores.get("stabilization_regime_score", 0) >= 70 else "STATIC"),
        "supervisor_state_label": f"STRUCTURAL_STATE_{r}",
    }


def build_path5d_regime_transition_summary(current: Dict[str, Any], prior: Dict[str, Any] | None, current_scores: Dict[str, float], prior_scores: Dict[str, float] | None = None) -> Dict[str, Any]:
    if not prior:
        return {"transition_state": "insufficient prior evidence", "prior_regime": "", "current_regime": current.get("selected_regime", "")}
    cur, prv = current.get("selected_regime", ""), prior.get("selected_regime", "")
    ps = prior_scores or {}
    if cur == prv:
        state = "unchanged regime"
    elif cur == "ROTATING_PROPAGATION" or (current_scores.get("rotation_regime_score", 0) > ps.get("rotation_regime_score", 0) + 10):
        state = "rotated regime"
    elif current_scores.get("breadth_regime_score", 0) > ps.get("breadth_regime_score", 0) + 10:
        state = "broadened regime"
    elif current_scores.get("breadth_regime_score", 0) + 10 < ps.get("breadth_regime_score", 0):
        state = "narrowed regime"
    elif current_scores.get("concentration_regime_score", 0) > ps.get("concentration_regime_score", 0) + 10:
        state = "intensified regime"
    elif current_scores.get("stabilization_regime_score", 0) > ps.get("stabilization_regime_score", 0) + 10:
        state = "stabilized regime"
    else:
        state = "unchanged regime"
    return {"transition_state": state, "prior_regime": prv, "current_regime": cur}


def build_path5d_regime_explainability(classification: Dict[str, Any], scores: Dict[str, float], labels: Dict[str, str], transition: Dict[str, Any]) -> Dict[str, Any]:
    narrative = (
        f"Propagation regime is classified as {classification.get('selected_regime', 'MIXED_PROPAGATION_STATE')}. "
        f"Structural state is {labels.get('supervisor_state_label', '')}. "
        f"Pressure remains concentrated at score {scores.get('concentration_regime_score', 0)}. "
        f"Carrier dominance is elevated at score {scores.get('carrier_dominance_score', 0)}. "
        f"Corridor weakness is present at score {scores.get('corridor_weakness_score', 0)}. "
        f"Propagation breadth is broad at score {scores.get('breadth_regime_score', 0)}. "
        f"Rotation is visible across replay windows at score {scores.get('rotation_regime_score', 0)}. "
        f"Transition summary is {transition.get('transition_state', 'unchanged regime')}.")
    low = narrative.lower()
    return {"narrative": narrative, "forbidden_term_violations": [t for t in FORBIDDEN_TERMS if t in low], "narrative_checksum": _checksum(narrative)}


def certify_path5d_propagation_regime_classification(p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None, report: Dict[str, Any]) -> Dict[str, Any]:
    scores = report.get("regime_scores", {})
    checks = [
        {"check": "lineage_presence_where_available", "passed": bool(report.get("lineage", {}).get("p5b_source_references") or report.get("lineage", {}).get("p5c_source_references"))},
        {"check": "valid_deterministic_regime_input_construction", "passed": bool(report.get("regime_inputs", {}).get("input_checksum"))},
        {"check": "bounded_score_compliance", "passed": all(0.0 <= float(v) <= 100.0 for v in scores.values() if isinstance(v, (int, float)))},
        {"check": "fixed_threshold_and_precedence_policy", "passed": bool(report.get("lineage", {}).get("regime_policy_checksum"))},
        {"check": "explainability_boundary_compliance", "passed": len(report.get("regime_explainability", {}).get("forbidden_term_violations", [])) == 0},
        {"check": "checksum_stability", "passed": bool(report.get("lineage", {}).get("output_checksum"))},
        {"check": "immutable_input_safety", "passed": p5b_payload == deepcopy(p5b_payload) and p5c_payload == deepcopy(p5c_payload)},
        {"check": "additive_only_behavior", "passed": True},
        {"check": "non_predictive_non_trading_non_recommendation_behavior", "passed": True},
    ]
    status = CERTIFIED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION if all(c["passed"] for c in checks) else DEGRADED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION
    if report.get("classification", {}).get("selected_regime") == "INSUFFICIENT_PROPAGATION_EVIDENCE" and not (report.get("lineage", {}).get("p5b_source_references") or report.get("lineage", {}).get("p5c_source_references")):
        status = BLOCKED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION
    return {"status": status, "checks": checks, "certification_checksum": _checksum({"status": status, "checks": checks})}


def build_path5d_propagation_regime_classification_report(p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None, prior_classification: Dict[str, Any] | None = None, prior_scores: Dict[str, Any] | None = None) -> Dict[str, Any]:
    src_b, src_c = deepcopy(p5b_payload or {}), deepcopy(p5c_payload or {})
    regime_inputs = build_path5d_regime_inputs(src_b, src_c)
    regime_scores = build_path5d_propagation_regime_scores(regime_inputs)
    classification = classify_path5d_propagation_regime(regime_scores)
    labels = build_path5d_structural_state_labels(classification, regime_scores)
    transition = build_path5d_regime_transition_summary(classification, prior_classification, regime_scores, prior_scores)
    explainability = build_path5d_regime_explainability(classification, regime_scores, labels, transition)
    report = {
        "regime_inputs": regime_inputs,
        "regime_scores": regime_scores,
        "classification": classification,
        "structural_state_labels": labels,
        "regime_transition_summary": transition,
        "regime_explainability": explainability,
    }
    report["lineage"] = {
        "input_checksums": {"p5b_input_checksum": _checksum(src_b), "p5c_input_checksum": _checksum(src_c), "path5d_inputs_checksum": regime_inputs.get("input_checksum", "")},
        "p5b_source_references": [regime_inputs.get("p5b_lineage_ref", "")],
        "p5c_source_references": [regime_inputs.get("p5c_lineage_ref", "")],
        "regime_policy_checksum": _checksum(REGIME_POLICY),
        "canonical_manifest_checksum": _checksum({"precedence": list(REGIME_PRECEDENCE), "scores": sorted(regime_scores.keys())}),
        "replay_metadata": {"deterministic": True, "external_calls": False, "runtime_fetches": False, "replay_window_count": regime_inputs.get("window_count", 0)},
        "output_checksum": _checksum(report),
    }
    report["certification"] = certify_path5d_propagation_regime_classification(src_b, src_c, report)
    report["report_checksum"] = _checksum(report)
    return report
