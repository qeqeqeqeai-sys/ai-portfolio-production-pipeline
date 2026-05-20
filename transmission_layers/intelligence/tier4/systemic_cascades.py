from __future__ import annotations
from typing import Any

from .cascade_boundaries import score_cascade_boundaries
from .cascade_corridors import score_cascade_corridors
from .cascade_signatures import compute_cascade_checksum, compute_systemic_cascade_checksum
from .dependency_concentration import score_dependency_concentration
from .structural_criticality import score_structural_criticality
from .systemic_bottlenecks import score_systemic_bottlenecks


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def _dominant_factor(payload: dict[str, Any]) -> str:
    factors = [
        ("structural_criticality", float(payload.get("structural_criticality_score", 0.0))),
        ("systemic_cascade", float(payload.get("systemic_cascade_score", 0.0))),
        ("cascade_corridor", float(payload.get("cascade_corridor_score", 0.0))),
        ("systemic_bottleneck", float(payload.get("systemic_bottleneck_score", 0.0))),
        ("dependency_concentration", float(payload.get("dependency_concentration_score", 0.0))),
        ("cascade_boundary", float(payload.get("cascade_boundary_weakness_score", 0.0))),
    ]
    factors.sort(key=lambda x: (-x[1], x[0]))
    return factors[0][0]


def build_cascade_intelligence(node: dict[str, Any], nodes: list[dict[str, Any]], edges: list[dict[str, Any]], node_stress: dict[str, float], suppression_ratio: float, failed_ratio: float, propagation: float) -> dict[str, Any]:
    critical = score_structural_criticality(node)
    bottleneck = score_systemic_bottlenecks(nodes, node_stress)
    deps = score_dependency_concentration(edges)
    corridor = score_cascade_corridors(edges, node_stress)
    systemic_score = _bound01(0.35 * critical["structural_criticality_score"] + 0.2 * bottleneck["systemic_bottleneck_score"] + 0.2 * deps["dependency_concentration_score"] + 0.15 * corridor["cascade_corridor_score"] + 0.1 * propagation)
    escalation = _bound01(0.5 * systemic_score + 0.5 * suppression_ratio)
    boundary = score_cascade_boundaries(suppression_ratio, failed_ratio, systemic_score)
    out = {
        "cascade_id": critical["cascade_id"],
        "structural_criticality_score": critical["structural_criticality_score"],
        "bounded_structural_criticality_score": critical["bounded_structural_criticality_score"],
        "systemic_cascade_score": systemic_score,
        "cascade_corridor_score": corridor["cascade_corridor_score"],
        "systemic_bottleneck_score": bottleneck["systemic_bottleneck_score"],
        "dependency_concentration_score": deps["dependency_concentration_score"],
        "cascade_boundary_weakness_score": boundary["cascade_boundary_weakness_score"],
        "local_to_systemic_destabilization_score": boundary["local_to_systemic_destabilization_score"],
        "survivability_continuity_score": boundary["survivability_continuity_score"],
        "cascade_escalation_score": escalation,
    }
    out["dominant_cascade_factor"] = _dominant_factor(out)
    out["cascade_classification"] = "critical" if escalation >= 0.75 else "elevated" if escalation >= 0.45 else "contained"
    out["structural_criticality_checksum"] = critical["structural_criticality_checksum"]
    out["systemic_cascade_checksum"] = compute_systemic_cascade_checksum({"systemic_cascade_score": systemic_score, "cascade_escalation_score": escalation})
    out["cascade_corridor_checksum"] = corridor["cascade_corridor_checksum"]
    out["bottleneck_checksum"] = bottleneck["bottleneck_checksum"]
    out["dependency_concentration_checksum"] = deps["dependency_concentration_checksum"]
    out["cascade_boundary_checksum"] = boundary["cascade_boundary_checksum"]
    out["cascade_checksum"] = compute_cascade_checksum(out)
    return out


def order_cascades(cascades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        cascades,
        key=lambda c: (
            -float(c.get("structural_criticality_score", 0.0)),
            -float(c.get("systemic_cascade_score", 0.0)),
            -float(c.get("cascade_escalation_score", 0.0)),
            -float(c.get("dependency_concentration_score", 0.0)),
            -float(c.get("systemic_bottleneck_score", 0.0)),
            float(c.get("survivability_continuity_score", 0.0)),
            -float(c.get("cascade_boundary_weakness_score", 0.0)),
            str(c.get("cascade_id", "")),
        ),
    )
