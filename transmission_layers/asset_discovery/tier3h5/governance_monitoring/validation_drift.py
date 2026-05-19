from __future__ import annotations
from typing import Any

def validation_drift(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    c = current.get("inputs", {}).get("logs/tier3h5_orchestration_guardrails.json", {})
    b = baseline.get("inputs", {}).get("logs/tier3h5_orchestration_guardrails.json", {})
    return {"validation_status_drift": c.get("validation_results", []) != b.get("validation_results", [])}
