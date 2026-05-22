"""Tier 7A deterministic strategic graph-state classification."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from transmission_layers.operationalization.serialization import stable_checksum

STRATEGIC_STATES: Tuple[str, ...] = (
    "stable",
    "stressed",
    "fragile",
    "distorted",
    "fragmented",
    "transitional",
    "regime_shifting",
    "degraded",
    "structurally_blocked",
    "invalid_input",
)

# deterministic precedence (highest to lowest severity)
STATE_PRECEDENCE: Tuple[str, ...] = (
    "invalid_input",
    "structurally_blocked",
    "degraded",
    "regime_shifting",
    "fragmented",
    "distorted",
    "fragile",
    "transitional",
    "stressed",
    "stable",
)

THRESHOLDS: Dict[str, float] = {
    "fragile_health_max": 0.25,
    "stressed_health_max": 0.45,
    "transitional_health_max": 0.65,
    "stable_health_min": 0.85,
    "distorted_distortion_min": 0.60,
    "regime_shift_min": 0.70,
    "fragmented_ratio_min": 0.30,
    "degraded_quality_max": 0.40,
    "blocked_ratio_min": 0.60,
}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded(value: Any) -> float:
    return max(0.0, min(1.0, round(_as_float(value, 0.0), 6)))


def _sorted_nodes(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    nodes = payload.get("nodes", [])
    if not isinstance(nodes, list):
        return []
    return sorted((dict(n) for n in nodes if isinstance(n, dict)), key=lambda n: str(n.get("node_id", "")))


def _sorted_edges(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    edges = payload.get("edges", [])
    if not isinstance(edges, list):
        return []

    def _key(e: Dict[str, Any]) -> Tuple[str, str, str]:
        src = str(e.get("source_node_id", ""))
        dst = str(e.get("target_node_id", ""))
        eid = str(e.get("edge_id", f"{src}->{dst}"))
        return (src, dst, eid)

    return sorted((dict(e) for e in edges if isinstance(e, dict)), key=_key)


def classify_strategic_graph_state(evidence: Dict[str, Any]) -> Dict[str, Any]:
    input_safe = deepcopy(evidence) if isinstance(evidence, dict) else {}

    malformed_input = not isinstance(evidence, dict)
    nodes = _sorted_nodes(input_safe)
    edges = _sorted_edges(input_safe)

    node_ids = {str(n.get("node_id", "")) for n in nodes if str(n.get("node_id", "")).strip()}
    edge_count = len(edges)

    empty_graph = len(nodes) == 0 and edge_count == 0
    disconnected_edges = 0
    blocked_edges = 0
    degraded_edges = 0

    for edge in edges:
        src = str(edge.get("source_node_id", "")).strip()
        dst = str(edge.get("target_node_id", "")).strip()
        if src not in node_ids or dst not in node_ids or src == "" or dst == "":
            disconnected_edges += 1

        if bool(edge.get("suppressed_for_propagation", False)):
            blocked_edges += 1

        quality = _bounded(edge.get("edge_quality_score", 1.0))
        if quality <= THRESHOLDS["degraded_quality_max"]:
            degraded_edges += 1

    invalid_structure = (
        malformed_input
        or not isinstance(input_safe.get("nodes", []), list)
        or not isinstance(input_safe.get("edges", []), list)
        or any(not isinstance(n, dict) for n in input_safe.get("nodes", []))
        or any(not isinstance(e, dict) for e in input_safe.get("edges", []))
    )

    health_score = _bounded(input_safe.get("graph_health_score", input_safe.get("structural_health_score", 1.0)))
    distortion_score = _bounded(input_safe.get("distortion_score", 0.0))
    transition_pressure = _bounded(input_safe.get("transition_pressure_score", 0.0))
    regime_shift_signal = _bounded(input_safe.get("regime_shift_signal", 0.0))

    fragmentation_ratio = round(disconnected_edges / max(1, edge_count), 6)
    blocked_ratio = round(blocked_edges / max(1, edge_count), 6)
    degraded_ratio = round(degraded_edges / max(1, edge_count), 6)

    conditions = {
        "invalid_input": bool(invalid_structure),
        "structurally_blocked": bool(blocked_ratio >= THRESHOLDS["blocked_ratio_min"] and edge_count > 0),
        "degraded": bool(degraded_ratio >= 0.5 or health_score <= THRESHOLDS["fragile_health_max"]),
        "regime_shifting": bool(regime_shift_signal >= THRESHOLDS["regime_shift_min"]),
        "fragmented": bool(empty_graph or (fragmentation_ratio >= THRESHOLDS["fragmented_ratio_min"] and edge_count > 0)),
        "distorted": bool(distortion_score >= THRESHOLDS["distorted_distortion_min"]),
        "fragile": bool(health_score <= THRESHOLDS["stressed_health_max"]),
        "transitional": bool(
            transition_pressure >= 0.5
            or (THRESHOLDS["stressed_health_max"] < health_score <= THRESHOLDS["transitional_health_max"])
        ),
        "stressed": bool(health_score < THRESHOLDS["stable_health_min"]),
        "stable": True,
    }

    strategic_state = "stable"
    trigger = "default_stable"
    for state in STATE_PRECEDENCE:
        if conditions[state]:
            strategic_state = state
            trigger = f"condition:{state}"
            break

    evidence_summary = {
        "node_count": len(nodes),
        "edge_count": edge_count,
        "empty_graph": empty_graph,
        "fragmentation_ratio": fragmentation_ratio,
        "blocked_ratio": blocked_ratio,
        "degraded_ratio": degraded_ratio,
        "health_score": health_score,
        "distortion_score": distortion_score,
        "transition_pressure": transition_pressure,
        "regime_shift_signal": regime_shift_signal,
    }

    explanation = (
        "Strategic graph-state classification is deterministic: "
        f"state={strategic_state}; trigger={trigger}; nodes={len(nodes)}; edges={edge_count}; "
        f"health={health_score:.6f}; distortion={distortion_score:.6f}; "
        f"fragmentation={fragmentation_ratio:.6f}; blocked={blocked_ratio:.6f}."
    )

    result = {
        "strategic_graph_state": strategic_state,
        "strategic_state_precedence": list(STATE_PRECEDENCE),
        "thresholds": dict(THRESHOLDS),
        "evidence_summary": evidence_summary,
        "explanation": explanation,
        "invariant_flags": {
            "deterministic_output": True,
            "replay_compatible": True,
            "immutable_input_safe": True,
            "no_runtime_mutation": True,
            "no_adaptive_control": True,
            "no_prediction_engine": True,
            "additive_only": True,
        },
    }
    result["strategic_graph_state_checksum"] = stable_checksum(
        {
            "strategic_graph_state": result["strategic_graph_state"],
            "evidence_summary": result["evidence_summary"],
            "invariant_flags": result["invariant_flags"],
            "thresholds": result["thresholds"],
        },
        prefix="tier7a_strategic_state",
    )
    return result


__all__ = [
    "STRATEGIC_STATES",
    "STATE_PRECEDENCE",
    "THRESHOLDS",
    "classify_strategic_graph_state",
]
