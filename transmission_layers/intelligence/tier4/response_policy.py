from __future__ import annotations

from typing import Any, Dict, List

from .response_effectiveness import compute_response_effectiveness, summarize_response_effectiveness
from .response_explanations import explain_response_policy
from .response_signatures import compute_response_checksum, compute_response_signature_checksum
from .scenario_semantics import clamp_score


def _node_key(node: Dict[str, Any]) -> tuple:
    return (-float(node.get("traffic_score", 0.0)), -float(node.get("fragmentation_score", 0.0)), float(node.get("resilience_score", 0.0)), -float(node.get("contagion_score", 0.0)), str(node.get("node_id", "")))


def _edge_key(edge: Dict[str, Any]) -> tuple:
    cid = f"{edge.get('source_node_id','')}->{edge.get('target_node_id','')}"
    return (-float(edge.get("overload_contribution", edge.get("edge_quality_score", 0.0))), -float(edge.get("fragmentation_contribution", 1.0 - float(edge.get("edge_quality_score", 0.0)))), float(edge.get("resilience_contribution", 1.0)), -float(edge.get("cascade_contribution", 0.0)), cid)


def generate_structural_response_policy(state_before: Dict[str, Any], state_after: Dict[str, Any], top_k: int = 3) -> Dict[str, Any]:
    nodes = sorted(state_before.get("structural_influence_nodes", []), key=_node_key)
    edges = sorted(state_before.get("quality_scored_edges", []), key=_edge_key)
    k = max(0, min(int(top_k), 10))
    target_nodes = [str(n.get("node_id", "")) for n in nodes[:k]]
    target_corridors = [f"{e.get('source_node_id','')}->{e.get('target_node_id','')}" for e in edges[:k]]
    effectiveness = compute_response_effectiveness(state_before, state_after)
    summary = summarize_response_effectiveness(effectiveness)
    score = clamp_score(effectiveness.get("response_effectiveness_score", 0.0))
    response_type = "reinforce_resilience" if score >= 0.5 else "limited_recovery"
    out = {
        "response_policy_id": f"response_{compute_response_checksum({'n': target_nodes, 'c': target_corridors, 't': response_type})[:12]}",
        "response_type": response_type,
        "target_nodes": target_nodes,
        "target_corridors": target_corridors,
        "expected_structural_effect": "instability_reduction",
        "response_priority": "high" if score >= 0.66 else ("medium" if score >= 0.33 else "low"),
        "response_score": score,
        "bounded_effectiveness_score": score,
        "deterministic_rationale": explain_response_policy(response_type, effectiveness.get("effectiveness_deltas", {})),
    }
    out["response_checksum"] = compute_response_checksum(out)
    out["response_signature_checksum"] = compute_response_signature_checksum({"policy": out, "effectiveness": effectiveness})
    out["diagnostics"] = {
        "response_policy_id": out["response_policy_id"],
        "response_type": out["response_type"],
        "response_checksum": out["response_checksum"],
        "response_effectiveness_score": score,
        "response_signature_checksum": out["response_signature_checksum"],
        "response_recovery_detected": bool(score > 0.5),
        "dominant_response_factor": summary.get("dominant_response_factor", "none"),
        "response_consistency_valid": bool(out["response_checksum"]),
        "response_replay_window_size": 0,
    }
    return out
