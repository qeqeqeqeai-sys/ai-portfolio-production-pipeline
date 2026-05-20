from __future__ import annotations

from typing import Any

from .contagion_signatures import compute_stress_concentration_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_stress_concentration(node_states: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = sorted((dict(n) for n in node_states), key=lambda x: str(x.get("node_id", "")))
    if not nodes:
        out = {
            "stress_concentration_score": 0.0,
            "bounded_stress_concentration_score": 0.0,
            "local_to_systemic_escalation_score": 0.0,
            "stress_concentration_detected": False,
        }
        out["stress_concentration_checksum"] = compute_stress_concentration_checksum(out)
        return out
    stresses = [_b(n.get("stress", n.get("propagated_stress", 0.0))) for n in nodes]
    max_stress = max(stresses)
    mean_stress = sum(stresses) / len(stresses)
    concentration = _b(max_stress - mean_stress + (max_stress * 0.5))
    escalation = _b((sum(1 for s in stresses if s >= 0.75) / len(stresses)) * max_stress)
    out = {
        "stress_concentration_score": concentration,
        "bounded_stress_concentration_score": concentration,
        "local_to_systemic_escalation_score": escalation,
        "stress_concentration_detected": concentration >= 0.55,
    }
    out["stress_concentration_checksum"] = compute_stress_concentration_checksum(out)
    return out
