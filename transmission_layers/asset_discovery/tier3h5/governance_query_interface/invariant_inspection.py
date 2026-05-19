from __future__ import annotations

from typing import Any


def build_invariant_inspection(results: dict[str, Any]) -> dict[str, Any]:
    invariants = [r for r in results.get("results", []) if r.get("query_type") in {"list_invariants", "inspect_invariant"}]
    return {"invariant_inspections_generated": len(invariants), "records": invariants}
