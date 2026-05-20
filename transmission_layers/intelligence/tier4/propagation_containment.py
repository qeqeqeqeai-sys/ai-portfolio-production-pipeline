from __future__ import annotations

from typing import Any

from .contagion_signatures import compute_propagation_containment_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_propagation_containment(corridors: list[dict[str, Any]]) -> dict[str, Any]:
    edges = sorted((dict(e) for e in corridors), key=lambda x: str(x.get("corridor_id", "")))
    if not edges:
        out = {"propagation_containment_score": 1.0, "stress_absorption_score": 1.0, "stress_transmission_score": 0.0}
        out["propagation_containment_checksum"] = compute_propagation_containment_checksum(out)
        return out
    containment = [_b(e.get("containment", 0.0)) for e in edges]
    transmission = [_b(e.get("exit_stress", 0.0)) for e in edges]
    containment_score = _b(sum(containment) / len(containment))
    transmission_score = _b(sum(transmission) / len(transmission))
    absorption_score = _b(containment_score * (1.0 - transmission_score * 0.5))
    out = {
        "propagation_containment_score": containment_score,
        "stress_absorption_score": absorption_score,
        "stress_transmission_score": transmission_score,
    }
    out["propagation_containment_checksum"] = compute_propagation_containment_checksum(out)
    return out
