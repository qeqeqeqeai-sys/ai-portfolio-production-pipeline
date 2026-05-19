from __future__ import annotations
from typing import Any

def readiness_drift(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    c = current.get("inputs", {}).get("logs/tier3h5_upload_coordination_summary.json", {})
    b = baseline.get("inputs", {}).get("logs/tier3h5_upload_coordination_summary.json", {})
    return {
        "dashboard_readiness_drift": c.get("dashboard_inventory", []) != b.get("dashboard_inventory", []),
        "semantic_layer_readiness_drift": c.get("semantic_layer_ready") != b.get("semantic_layer_ready"),
        "smoke_test_drift": c.get("smoke_tests", []) != b.get("smoke_tests", []),
        "operational_readiness_drift": c.get("operational_readiness") != b.get("operational_readiness"),
    }
