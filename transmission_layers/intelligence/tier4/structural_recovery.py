from __future__ import annotations

from typing import Any

from .recovery_bottlenecks import score_recovery_bottlenecks
from .recovery_corridors import score_recovery_corridors
from .recovery_explanations import explain_structural_recovery
from .recovery_fragments import score_recovery_fragments
from .recovery_signatures import (
    compute_recovery_bottleneck_checksum,
    compute_recovery_checksum,
    compute_recovery_corridor_checksum,
    compute_recovery_fragmentation_checksum,
    compute_recovery_signature_checksum,
    compute_regeneration_checksum,
    compute_reintegration_checksum,
    compute_structural_recovery_checksum,
)
from .regeneration_pathways import score_regeneration_pathways
from .reintegration_stability import score_reintegration_stability


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def analyze_structural_recovery(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], replay_window: list[dict[str, float]]) -> dict[str, Any]:
    ordered_nodes = sorted((dict(n) for n in nodes), key=lambda x: str(x.get("node_id", "")))
    ordered_edges = sorted((dict(e) for e in edges), key=lambda x: (str(x.get("source_node_id", "")), str(x.get("target_node_id", ""))))
    node_recovery = {
        node_id: _bound01(float(replay_window[-1].get(node_id, 0.0)) if replay_window else 0.0)
        for node_id in sorted(str(n.get("node_id", "")) for n in ordered_nodes)
    }
    base_recovery = _bound01(sum(node_recovery.values()) / len(node_recovery) if node_recovery else 0.0)

    corridors = score_recovery_corridors(ordered_edges, node_recovery)
    regen = score_regeneration_pathways(ordered_nodes, replay_window)
    bottlenecks = score_recovery_bottlenecks(ordered_nodes, node_recovery)
    fragments = score_recovery_fragments(ordered_edges, node_recovery)
    reintegration = score_reintegration_stability(base_recovery, fragments["recovery_fragmentation_score"], bottlenecks["recovery_bottleneck_score"])

    relapse = _bound01(1.0 - regen["regeneration_pathway_score"])
    survivability = _bound01(0.55 * base_recovery + 0.45 * reintegration["reintegration_stability_score"])
    continuity = _bound01(0.5 * survivability + 0.5 * (1.0 - bottlenecks["recovery_bottleneck_score"]))

    factors = sorted([
        ("recovery_corridor_score", corridors["recovery_corridor_score"]),
        ("regeneration_pathway_score", regen["regeneration_pathway_score"]),
        ("reintegration_stability_score", reintegration["reintegration_stability_score"]),
        ("survivability_restoration_score", survivability),
    ], key=lambda x: (-x[1], x[0]))
    dominant = factors[0][0] if factors else "none"

    result = {
        "recovery_id": "tier4n-recovery",
        "structural_recovery_score": base_recovery,
        "bounded_structural_recovery_score": base_recovery,
        "recovery_corridor_score": corridors["recovery_corridor_score"],
        "regeneration_pathway_score": regen["regeneration_pathway_score"],
        "reintegration_stability_score": reintegration["reintegration_stability_score"],
        "recovery_bottleneck_score": bottlenecks["recovery_bottleneck_score"],
        "recovery_fragmentation_score": fragments["recovery_fragmentation_score"],
        "survivability_restoration_score": survivability,
        "recovery_relapse_score": relapse,
        "post_cascade_continuity_score": continuity,
        "dominant_recovery_factor": dominant,
        "recovery_classification": "stabilizing" if base_recovery >= 0.6 and relapse <= 0.4 else "relapse-prone" if relapse >= 0.6 else "partial-recovery",
        "structural_recovery_detected": base_recovery >= 0.5,
        "recovery_corridor_detected": corridors["recovery_corridor_detected"],
        "regeneration_detected": regen["regeneration_detected"],
        "reintegration_stability_detected": reintegration["reintegration_stability_detected"],
        "recovery_bottleneck_detected": bottlenecks["recovery_bottleneck_detected"],
        "recovery_fragmentation_detected": fragments["recovery_fragmentation_detected"],
        "survivability_restoration_detected": survivability >= 0.5,
        "recovery_relapse_detected": relapse >= 0.5,
        "recovery_consistency_valid": True,
        "recovery_replay_window_size": len(replay_window),
    }
    result["structural_recovery_checksum"] = compute_structural_recovery_checksum(result)
    result["recovery_corridor_checksum"] = compute_recovery_corridor_checksum(corridors)
    result["regeneration_checksum"] = compute_regeneration_checksum(regen)
    result["reintegration_checksum"] = compute_reintegration_checksum(reintegration)
    result["recovery_bottleneck_checksum"] = compute_recovery_bottleneck_checksum(bottlenecks)
    result["recovery_fragmentation_checksum"] = compute_recovery_fragmentation_checksum(fragments)
    result["recovery_signature_checksum"] = compute_recovery_signature_checksum(result)
    result["recovery_checksum"] = compute_recovery_checksum(result)
    result["explanation"] = explain_structural_recovery(result)
    return result
