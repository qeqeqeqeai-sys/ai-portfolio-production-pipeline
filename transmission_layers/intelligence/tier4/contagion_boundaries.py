from __future__ import annotations

from typing import Any

from .containment_integrity import compute_containment_integrity
from .contagion_signatures import compute_contagion_boundary_checksum, compute_contagion_checksum
from .propagation_containment import compute_propagation_containment
from .stress_amplification import compute_stress_amplification
from .stress_concentration import compute_stress_concentration
from .stress_leakage import compute_stress_leakage


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_contagion_boundaries(corridors: list[dict[str, Any]]) -> dict[str, Any]:
    edges = sorted((dict(e) for e in corridors), key=lambda x: str(x.get("corridor_id", "")))
    if not edges:
        out = {"contagion_boundary_score": 1.0, "contagion_boundary_detected": True}
        out["contagion_boundary_checksum"] = compute_contagion_boundary_checksum(out)
        return out
    blocked = sum(1 for e in edges if _b(e.get("containment", 0.0)) >= 0.6)
    score = _b(blocked / len(edges))
    out = {"contagion_boundary_score": score, "contagion_boundary_detected": score >= 0.4}
    out["contagion_boundary_checksum"] = compute_contagion_boundary_checksum(out)
    return out


def compute_contagion_intelligence(contagion_id: str, node_states: list[dict[str, Any]], corridors: list[dict[str, Any]], replay_window: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    replay_entries = sorted((dict(e) for e in (replay_window or [])), key=lambda x: str(x.get("tick", x.get("step", ""))))
    sc = compute_stress_concentration(node_states)
    sa = compute_stress_amplification(corridors)
    cb = compute_contagion_boundaries(corridors)
    ci = compute_containment_integrity(corridors)
    sl = compute_stress_leakage(corridors)
    pc = compute_propagation_containment(corridors)
    factors = sorted([
        ("stress_concentration_score", sc["stress_concentration_score"]),
        ("stress_amplification_score", sa["stress_amplification_score"]),
        ("contagion_boundary_score", cb["contagion_boundary_score"]),
        ("containment_integrity_risk", 1.0 - ci["containment_integrity_score"]),
        ("stress_leakage_score", sl["stress_leakage_score"]),
        ("containment_breach_score", sl["containment_breach_score"]),
        ("local_to_systemic_escalation_score", sc["local_to_systemic_escalation_score"]),
    ], key=lambda x: (-x[1], x[0]))
    dominant_factor = factors[0][0] if factors else "none"
    risk = _b(sum(v for _, v in factors) / len(factors)) if factors else 0.0
    classification = "contained" if risk < 0.34 else "boundary_watch" if risk < 0.67 else "contagious"
    out = {
        "contagion_id": str(contagion_id),
        "stress_concentration_score": sc["stress_concentration_score"],
        "bounded_stress_concentration_score": sc["bounded_stress_concentration_score"],
        "stress_amplification_score": sa["stress_amplification_score"],
        "contagion_boundary_score": cb["contagion_boundary_score"],
        "containment_integrity_score": ci["containment_integrity_score"],
        "stress_leakage_score": sl["stress_leakage_score"],
        "propagation_containment_score": pc["propagation_containment_score"],
        "local_to_systemic_escalation_score": sc["local_to_systemic_escalation_score"],
        "containment_breach_score": sl["containment_breach_score"],
        "stress_absorption_score": pc["stress_absorption_score"],
        "stress_transmission_score": pc["stress_transmission_score"],
        "dominant_contagion_factor": dominant_factor,
        "contagion_classification": classification,
        "stress_concentration_detected": sc["stress_concentration_detected"],
        "stress_amplifier_detected": sa["stress_amplifier_detected"],
        "contagion_boundary_detected": cb["contagion_boundary_detected"],
        "containment_weakening_detected": ci["containment_weakening_detected"],
        "stress_leakage_detected": sl["stress_leakage_detected"],
        "containment_breach_detected": sl["containment_breach_detected"],
        "local_to_systemic_escalation_detected": sc["local_to_systemic_escalation_score"] >= 0.3,
        "contagion_replay_window_size": len(replay_entries),
        "stress_concentration_checksum": sc["stress_concentration_checksum"],
        "stress_amplification_checksum": sa["stress_amplification_checksum"],
        "contagion_boundary_checksum": cb["contagion_boundary_checksum"],
        "containment_integrity_checksum": ci["containment_integrity_checksum"],
        "stress_leakage_checksum": sl["stress_leakage_checksum"],
        "propagation_containment_checksum": pc["propagation_containment_checksum"],
    }
    out["contagion_checksum"] = compute_contagion_checksum(out)
    out["contagion_consistency_valid"] = out["contagion_checksum"] == compute_contagion_checksum(out)
    return out
