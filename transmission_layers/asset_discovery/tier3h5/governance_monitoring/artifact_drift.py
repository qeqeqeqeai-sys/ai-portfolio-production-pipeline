from __future__ import annotations
from typing import Any

def artifact_drift(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    c = current.get("inputs", {}).get("logs/tier3h5_artifact_coordination_summary.json", {})
    b = baseline.get("inputs", {}).get("logs/tier3h5_artifact_coordination_summary.json", {})
    return {"artifact_inventory_drift": c.get("artifact_inventory", []) != b.get("artifact_inventory", [])}
