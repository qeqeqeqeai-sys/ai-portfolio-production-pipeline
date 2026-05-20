from __future__ import annotations

from typing import Any

from .transition_signatures import compute_regime_transition_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_regime_transition_pressure(node_states: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted((dict(s) for s in node_states), key=lambda x: str(x.get("node_id", "")))
    if not ordered:
        out = {"regime_transition_pressure_score": 0.0, "transition_pressure_detected": False}
        out["regime_transition_checksum"] = compute_regime_transition_checksum(out)
        return out
    stress = [_b(s.get("stress", s.get("propagated_stress", 0.0))) for s in ordered]
    overload = [_b(s.get("overload", 0.0)) for s in ordered]
    pressure = _b(((sum(stress) / len(stress)) * 0.5) + ((sum(overload) / len(overload)) * 0.5))
    out = {"regime_transition_pressure_score": pressure, "transition_pressure_detected": pressure >= 0.55}
    out["regime_transition_checksum"] = compute_regime_transition_checksum(out)
    return out

from .fragmentation_diagnostics import compute_fragmentation_diagnostics
from .resilience_dispersion import compute_resilience_dispersion
from .structural_entropy import compute_structural_entropy
from .systemic_stress_clustering import compute_systemic_stress_clustering
from .topology_coherence import compute_topology_coherence
from .transition_signatures import compute_transition_checksum, compute_transition_signature_checksum


def _classify(score: float) -> str:
    if score >= 0.8:
        return "phase_shift_imminent"
    if score >= 0.6:
        return "transition_risk_elevated"
    if score >= 0.4:
        return "transition_watch"
    return "structurally_stable"


def compute_transition_diagnostics(node_states: list[dict[str, Any]], corridors: list[dict[str, Any]], transition_id: str = "tier4_transition") -> dict[str, Any]:
    nodes = [dict(s) for s in sorted(node_states, key=lambda x: str(x.get("node_id", "")))]
    edges = [dict(c) for c in sorted(corridors, key=lambda x: (str(x.get("from", "")), str(x.get("to", ""))))]

    entropy = compute_structural_entropy(nodes)
    pressure = compute_regime_transition_pressure(nodes)
    coherence = compute_topology_coherence(nodes, edges)
    frag = compute_fragmentation_diagnostics(edges)
    dispersion = compute_resilience_dispersion(nodes)
    clustering = compute_systemic_stress_clustering(nodes)

    survivability_boundary_weakening_score = _b((1.0 - coherence["topology_coherence_score"]) * 0.7 + frag["fragmentation_score"] * 0.3)
    structural_concentration_risk_score = _b(clustering["systemic_stress_clustering_score"] * 0.5 + pressure["regime_transition_pressure_score"] * 0.5)
    vulnerability = _b(
        pressure["regime_transition_pressure_score"] * 0.22
        + entropy["entropy_score"] * 0.18
        + (1.0 - coherence["topology_coherence_score"]) * 0.18
        + frag["fragmentation_score"] * 0.14
        + dispersion["resilience_dispersion_score"] * 0.12
        + clustering["systemic_stress_clustering_score"] * 0.08
        + structural_concentration_risk_score * 0.08
    )
    factors = sorted([
        ("regime_transition_pressure", pressure["regime_transition_pressure_score"]),
        ("structural_entropy", entropy["entropy_score"]),
        ("topology_coherence_loss", 1.0 - coherence["topology_coherence_score"]),
        ("fragmentation", frag["fragmentation_score"]),
        ("resilience_dispersion", dispersion["resilience_dispersion_score"]),
        ("systemic_stress_clustering", clustering["systemic_stress_clustering_score"]),
        ("structural_concentration_risk", structural_concentration_risk_score),
    ], key=lambda x: (-x[1], x[0]))

    out = {
        "transition_id": transition_id,
        "entropy_score": entropy["entropy_score"],
        "bounded_entropy_score": entropy["bounded_entropy_score"],
        "regime_transition_pressure_score": pressure["regime_transition_pressure_score"],
        "topology_coherence_score": coherence["topology_coherence_score"],
        "fragmentation_score": frag["fragmentation_score"],
        "resilience_dispersion_score": dispersion["resilience_dispersion_score"],
        "systemic_stress_clustering_score": clustering["systemic_stress_clustering_score"],
        "survivability_boundary_weakening_score": survivability_boundary_weakening_score,
        "structural_concentration_risk_score": structural_concentration_risk_score,
        "transition_vulnerability_score": vulnerability,
        "dominant_transition_factor": factors[0][0],
        "transition_classification": _classify(vulnerability),
        "transition_pressure_detected": pressure["transition_pressure_detected"],
        "entropy_accumulation_detected": entropy["entropy_accumulation_detected"],
        "topology_coherence_degradation_detected": coherence["topology_coherence_degradation_detected"],
        "fragmentation_detected": frag["fragmentation_detected"],
        "systemic_stress_cluster_detected": clustering["systemic_stress_cluster_detected"],
        "survivability_boundary_weakening_detected": survivability_boundary_weakening_score >= 0.5,
        "transition_consistency_valid": True,
        "transition_replay_window_size": len(nodes),
        "entropy_checksum": entropy["entropy_checksum"],
        "regime_transition_checksum": pressure["regime_transition_checksum"],
        "topology_coherence_checksum": coherence["topology_coherence_checksum"],
        "fragmentation_checksum": frag["fragmentation_checksum"],
        "dispersion_checksum": dispersion["dispersion_checksum"],
        "stress_clustering_checksum": clustering["stress_clustering_checksum"],
    }
    out["transition_signature_checksum"] = compute_transition_signature_checksum(out)
    out["transition_checksum"] = compute_transition_checksum(out)
    return out


def rank_transition_diagnostics(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [dict(i) for i in items],
        key=lambda x: (
            -float(x.get("regime_transition_pressure_score", 0.0)),
            -float(x.get("entropy_score", 0.0)),
            float(x.get("topology_coherence_score", 1.0)),
            -float(x.get("fragmentation_score", 0.0)),
            -float(x.get("resilience_dispersion_score", 0.0)),
            -float(x.get("systemic_stress_clustering_score", 0.0)),
            -float(x.get("structural_concentration_risk_score", 0.0)),
            str(x.get("transition_id", x.get("node_id", x.get("corridor_id", "")))),
        ),
    )
