from __future__ import annotations

from typing import Any

from .federation_common import clamp_score


def federation_boundary_enforcement_diagnostics(bridges: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(bridges, key=lambda b: (str(b.get("bridge_id", "")), str(b.get("source", "")), str(b.get("target", ""))))
    if not ordered:
        return {"federation_boundary_enforcement_score": 1.0}
    weak = sum(1 for b in ordered if float(b.get("boundary_strength", 1.0)) < float(b.get("minimum_boundary_strength", 0.5)))
    return {"federation_boundary_enforcement_score": clamp_score(1.0 - (weak / len(ordered)))}
