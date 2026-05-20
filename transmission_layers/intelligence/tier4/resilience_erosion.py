from __future__ import annotations

from typing import Any

from .persistence_signatures import compute_erosion_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_resilience_erosion(states: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = [dict(x) for x in sorted(states, key=lambda s: str(s.get("node_id", "")))]
    entries = []
    for state in ordered:
        start = _b(float(state.get("resilience_start", state.get("resilience", 0.0))))
        end = _b(float(state.get("resilience_end", state.get("resilience", 0.0))))
        erosion = _b(start - end)
        entries.append({"node_id": str(state.get("node_id", "")), "resilience_erosion_score": erosion})
    entries = sorted(entries, key=lambda x: (-x["resilience_erosion_score"], x["node_id"]))
    score = _b(sum(x["resilience_erosion_score"] for x in entries) / max(1, len(entries)))
    out = {"resilience_erosion_score": score, "node_erosion": entries, "erosion_detected": score > 0.0}
    out["erosion_checksum"] = compute_erosion_checksum(out)
    return out
