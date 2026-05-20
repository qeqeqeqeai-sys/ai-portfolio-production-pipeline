from __future__ import annotations

from typing import Any

from .persistence_signatures import compute_instability_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_chronic_instability(states: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = [dict(x) for x in sorted(states, key=lambda s: str(s.get("node_id", "")))]
    vals = []
    for state in ordered:
        volatility = _b(float(state.get("volatility", abs(float(state.get("stress", 0.0)) - float(state.get("resilience", 0.0))))))
        vals.append({"node_id": str(state.get("node_id", "")), "instability": volatility})
    vals = sorted(vals, key=lambda x: (-x["instability"], x["node_id"]))
    score = _b(sum(v["instability"] for v in vals) / max(1, len(vals)))
    out = {"chronic_instability_score": score, "chronic_instability_detected": score >= 0.4, "node_instability": vals}
    out["instability_checksum"] = compute_instability_checksum(out)
    return out
