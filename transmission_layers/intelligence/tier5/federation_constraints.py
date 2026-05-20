from __future__ import annotations

from typing import Any

from .federation_common import clamp_score


def federation_constraint_diagnostics(systems: list[dict[str, Any]], dependencies: list[dict[str, Any]]) -> dict[str, Any]:
    system_ids = sorted(str(s.get("system_id", s.get("id", ""))) for s in systems)
    dep_pairs = sorted((str(d.get("source", "")), str(d.get("target", ""))) for d in dependencies)
    if not system_ids:
        return {"federation_constraint_score": 0.0, "federation_constraint_recurrence_score": 0.0}
    external_edges = sum(1 for src, tgt in dep_pairs if src not in system_ids or tgt not in system_ids)
    duplicate_edges = len(dep_pairs) - len(set(dep_pairs))
    constraint_pressure = clamp_score((external_edges + duplicate_edges) / max(1, len(dep_pairs)))
    recurrence = clamp_score(duplicate_edges / max(1, len(dep_pairs)))
    return {
        "federation_constraint_score": constraint_pressure,
        "federation_constraint_recurrence_score": recurrence,
    }
