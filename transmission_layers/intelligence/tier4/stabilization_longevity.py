from __future__ import annotations

from typing import Any

from .persistence_signatures import compute_longevity_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_stabilization_longevity(states: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = [dict(x) for x in sorted(states, key=lambda s: str(s.get("node_id", "")))]
    vals = []
    for state in ordered:
        duration = max(0.0, float(state.get("stable_duration", 0.0)))
        norm = _b(duration / 10.0)
        vals.append({"node_id": str(state.get("node_id", "")), "longevity": norm})
    vals = sorted(vals, key=lambda x: (-x["longevity"], x["node_id"]))
    score = _b(sum(v["longevity"] for v in vals) / max(1, len(vals)))
    out = {"stabilization_longevity_score": score, "node_longevity": vals}
    out["longevity_checksum"] = compute_longevity_checksum(out)
    return out
