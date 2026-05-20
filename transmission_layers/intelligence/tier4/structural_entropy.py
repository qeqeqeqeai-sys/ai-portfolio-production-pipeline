from __future__ import annotations

from typing import Any

from .transition_signatures import compute_entropy_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_structural_entropy(node_states: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted((dict(s) for s in node_states), key=lambda x: str(x.get("node_id", "")))
    if not ordered:
        out = {"entropy_score": 0.0, "bounded_entropy_score": 0.0, "entropy_accumulation_detected": False}
        out["entropy_checksum"] = compute_entropy_checksum(out)
        return out
    stress = [_b(s.get("stress", s.get("propagated_stress", 0.0))) for s in ordered]
    spread = max(stress) - min(stress)
    mean = sum(stress) / len(stress)
    score = _b((spread * 0.6) + (mean * 0.4))
    out = {"entropy_score": score, "bounded_entropy_score": score, "entropy_accumulation_detected": score >= 0.5}
    out["entropy_checksum"] = compute_entropy_checksum(out)
    return out
