from __future__ import annotations

from typing import Any


def analyze_orchestration_trends(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    drift = any(s.get("orchestration_drift_detected") is True for s in summaries)
    return {
        "orchestration_stability_verified": not drift,
        "orchestration_drift_runs": sum(1 for s in summaries if s.get("orchestration_drift_detected") is True),
    }
