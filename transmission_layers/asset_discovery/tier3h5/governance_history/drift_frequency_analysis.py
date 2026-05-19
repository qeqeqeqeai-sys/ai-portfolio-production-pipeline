from __future__ import annotations

from typing import Any


def analyze_drift_frequency(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(summaries)
    drift_count = sum(1 for s in summaries if s.get("drift_detected") is True)
    recurring = drift_count >= 2
    pct = round((drift_count / total) * 100, 2) if total else 0.0
    return {
        "drift_runs": drift_count,
        "drift_frequency_percent": pct,
        "drift_frequency_detected": drift_count > 0,
        "recurring_drift_detected": recurring,
    }
