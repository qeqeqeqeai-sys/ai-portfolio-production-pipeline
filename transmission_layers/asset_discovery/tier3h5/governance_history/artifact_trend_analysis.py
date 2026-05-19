from __future__ import annotations

from typing import Any


def analyze_artifact_trends(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    artifact_drift = sum(1 for s in summaries if s.get("artifact_drift_detected") is True)
    skip_drift = sum(1 for s in summaries if s.get("optional_artifact_skip_drift_detected") is True)
    return {
        "artifact_consistency_verified": artifact_drift == 0,
        "artifact_drift_runs": artifact_drift,
        "optional_artifact_skip_frequency": round((skip_drift / len(summaries)) * 100, 2) if summaries else 0.0,
    }
