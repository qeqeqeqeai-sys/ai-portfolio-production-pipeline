from __future__ import annotations

from typing import Any


def analyze_readiness_trends(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    readiness_drift = sum(1 for s in summaries if s.get("readiness_drift_detected") is True)
    validation_drift = sum(1 for s in summaries if s.get("validation_drift_detected") is True)
    return {
        "readiness_continuity_verified": readiness_drift == 0 and validation_drift == 0,
        "readiness_drift_runs": readiness_drift,
        "validation_continuity_runs": len(summaries) - validation_drift,
    }
