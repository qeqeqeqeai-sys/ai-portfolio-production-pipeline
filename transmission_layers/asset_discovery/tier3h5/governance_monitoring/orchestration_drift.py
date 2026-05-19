from __future__ import annotations

from typing import Any


def orchestration_drift(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    c = current.get("inputs", {}).get("logs/tier3h5_orchestration_summary.json", {})
    b = baseline.get("inputs", {}).get("logs/tier3h5_orchestration_summary.json", {})
    c_stages = c.get("stages", []) if isinstance(c, dict) else []
    b_stages = b.get("stages", []) if isinstance(b, dict) else []
    c_names = [s.get("stage_name") for s in c_stages if isinstance(s, dict)]
    b_names = [s.get("stage_name") for s in b_stages if isinstance(s, dict)]
    required = [s.get("stage_name") for s in c_stages if isinstance(s, dict) and s.get("required") is True]
    req_missing = [s for s in required if s not in c_names]
    return {
        "stage_count_drift": len(c_names) != len(b_names),
        "required_stage_execution_drift": bool(req_missing),
        "optional_artifact_skip_drift_detected": c.get("optional_artifacts_skipped", []) != b.get("optional_artifacts_skipped", []),
    }
