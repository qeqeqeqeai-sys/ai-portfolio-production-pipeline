from __future__ import annotations

from typing import Any


def build_phase_inspection(results: dict[str, Any]) -> dict[str, Any]:
    records = [r for r in results.get("results", []) if "phase" in str(r.get("query_type", ""))]
    return {"phase_inspections_generated": len(records), "records": records}
