from __future__ import annotations

from typing import Any

from .adaptation_constraints import score_adaptation_constraints
from .adaptation_exhaustion import score_adaptation_exhaustion
from .flexibility_collapse import score_flexibility_collapse
from .reintegration_resistance import score_reintegration_resistance
from .resilience_saturation import score_resilience_saturation
from .rigidity_cascades import score_rigidity_cascades
from .rigidity_explanations import explain_structural_rigidity
from .rigidity_signatures import *


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def analyze_structural_rigidity(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], replay_window: list[dict[str, float]]) -> dict[str, Any]:
    ordered_nodes = sorted((dict(n) for n in nodes), key=lambda x: str(x.get("node_id", "")))
    ordered_edges = sorted((dict(e) for e in edges), key=lambda x: (str(x.get("source_node_id", "")), str(x.get("target_node_id", ""))))
    node_scores: dict[str, dict[str, Any]] = {}
    for n in ordered_nodes:
        nid = str(n.get("node_id", ""))
        resilience = _bound01(float(n.get("resilience_score", 0.5)))
        ac = score_adaptation_constraints(n, replay_window)
        rs = score_resilience_saturation(resilience, ac["adaptation_constraint_score"])
        fc = score_flexibility_collapse(ac["adaptation_constraint_score"], rs["resilience_saturation_score"])
        rr = score_reintegration_resistance(fc["flexibility_collapse_score"], resilience)
        ae = score_adaptation_exhaustion(ac["adaptation_constraint_score"], rr["reintegration_resistance_score"])
        node_scores[nid] = {**ac, **rs, **fc, **rr, **ae}

    for nid in sorted(node_scores):
        neighbors = sorted({str(e.get("target_node_id", "")) for e in ordered_edges if str(e.get("source_node_id", "")) == nid})
        neighbor_values = [node_scores[m]["flexibility_collapse_score"] for m in neighbors if m in node_scores]
        node_scores[nid].update(score_rigidity_cascades(neighbor_values, node_scores[nid]["flexibility_collapse_score"]))

    ranked = sorted(node_scores.items(), key=lambda kv: (-kv[1]["flexibility_collapse_score"], kv[0]))
    primary_id = ranked[0][0] if ranked else "tier4o-rigidity"
    primary = node_scores.get(primary_id, {k: 0.0 for k in ["adaptation_constraint_score", "resilience_saturation_score", "flexibility_collapse_score", "rigidity_cascade_score", "reintegration_resistance_score", "adaptation_exhaustion_score"]})
    structural_rigidity = _bound01((primary["adaptation_constraint_score"] + primary["resilience_saturation_score"] + primary["flexibility_collapse_score"] + primary["rigidity_cascade_score"] + primary["reintegration_resistance_score"] + primary["adaptation_exhaustion_score"]) / 6.0)
    structural_trapping = _bound01(0.5 * primary["flexibility_collapse_score"] + 0.5 * primary["reintegration_resistance_score"])
    adaptation_limit = _bound01(0.5 * primary["adaptation_exhaustion_score"] + 0.5 * primary["resilience_saturation_score"])

    factors = sorted([
        ("adaptation_constraint_score", primary["adaptation_constraint_score"]),
        ("resilience_saturation_score", primary["resilience_saturation_score"]),
        ("flexibility_collapse_score", primary["flexibility_collapse_score"]),
        ("adaptation_exhaustion_score", primary["adaptation_exhaustion_score"]),
        ("rigidity_cascade_score", primary["rigidity_cascade_score"]),
        ("reintegration_resistance_score", primary["reintegration_resistance_score"]),
    ], key=lambda x: (-x[1], x[0]))
    dominant = factors[0][0] if factors else "none"

    result = {
        "rigidity_id": primary_id,
        "structural_rigidity_score": structural_rigidity,
        "bounded_structural_rigidity_score": structural_rigidity,
        **primary,
        "structural_trapping_score": structural_trapping,
        "adaptation_limit_score": adaptation_limit,
        "dominant_rigidity_factor": dominant,
        "rigidity_classification": "rigid" if structural_rigidity >= 0.7 else "constrained" if structural_rigidity >= 0.45 else "adaptive",
        "structural_rigidity_detected": structural_rigidity >= 0.5,
        "structural_trapping_detected": structural_trapping >= 0.6,
        "rigidity_consistency_valid": True,
        "rigidity_replay_window_size": len(replay_window),
    }
    result["structural_rigidity_checksum"] = compute_structural_rigidity_checksum(result)
    result["adaptation_constraint_checksum"] = compute_adaptation_constraint_checksum(primary)
    result["resilience_saturation_checksum"] = compute_resilience_saturation_checksum(primary)
    result["flexibility_collapse_checksum"] = compute_flexibility_collapse_checksum(primary)
    result["rigidity_cascade_checksum"] = compute_rigidity_cascade_checksum(primary)
    result["reintegration_resistance_checksum"] = compute_reintegration_resistance_checksum(primary)
    result["adaptation_exhaustion_checksum"] = compute_adaptation_exhaustion_checksum(primary)
    result["rigidity_signature_checksum"] = compute_rigidity_signature_checksum(result)
    result["rigidity_checksum"] = compute_rigidity_checksum(result)
    result["explanation"] = explain_structural_rigidity(result)
    return result
