from __future__ import annotations

from typing import Any

from .transition_signatures import compute_dispersion_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_resilience_dispersion(node_states: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = sorted((dict(s) for s in node_states), key=lambda x: str(x.get("node_id", "")))
    if not nodes:
        out = {"resilience_dispersion_score": 0.0}
        out["dispersion_checksum"] = compute_dispersion_checksum(out)
        return out
    vals = [_b(n.get("resilience", 0.0)) for n in nodes]
    score = _b(max(vals) - min(vals))
    out = {"resilience_dispersion_score": score}
    out["dispersion_checksum"] = compute_dispersion_checksum(out)
    return out
