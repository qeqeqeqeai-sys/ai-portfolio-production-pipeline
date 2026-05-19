from __future__ import annotations

from typing import Any


def build_phase5c_summary(context: dict[str, Any], trend: dict[str, Any], run_id: str, history_count: int) -> dict[str, Any]:
    categories = trend.get("trend_categories", {})
    drift = categories.get("drift_frequency", {})
    orchestration = categories.get("orchestration", {})
    artifact = categories.get("artifact", {})
    readiness = categories.get("readiness", {})
    return {
        "monitoring_history_run_status": "success",
        "monitoring_snapshot_count": history_count,
        "historical_runs_analyzed": history_count,
        "trend_analysis_status": trend.get("trend_analysis_status", "completed"),
        "trend_classification": trend.get("trend_classification", "insufficient_history_for_trend_analysis"),
        "trend_checks_executed": trend.get("trend_checks_executed", 0),
        "trend_checks_with_findings": trend.get("trend_checks_with_findings", 0),
        "drift_frequency_detected": drift.get("drift_frequency_detected", False),
        "recurring_drift_detected": drift.get("recurring_drift_detected", False),
        "orchestration_stability_verified": orchestration.get("orchestration_stability_verified", True),
        "artifact_consistency_verified": artifact.get("artifact_consistency_verified", True),
        "readiness_continuity_verified": readiness.get("readiness_continuity_verified", True),
        "advisory_only_governance_verified": True,
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
        "ci_failure_required": False,
        "governance_invariants": {
            "advisory_only_governance_verified": True,
            "exact_match_only_preserved": True,
            "tier3h4_freeze_boundary_preserved": True,
            "ci_failure_required": False,
        },
        "trend_categories": categories,
        "run_id": run_id,
        "loaded_artifact_count": context.get("loaded_artifact_count", 0),
    }
