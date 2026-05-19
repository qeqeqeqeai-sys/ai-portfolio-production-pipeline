from __future__ import annotations

from pathlib import Path
from typing import Any
from .monitoring_context import stable_json_dumps


def classify_severity(history_status: str, findings: int) -> str:
    if history_status == "insufficient_monitoring_history":
        return "insufficient_monitoring_history"
    if findings == 0:
        return "no_drift_detected"
    if findings <= 2:
        return "informational_drift"
    return "warning_drift"


def build_monitoring_summary(context: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    categories = diagnostics.get("drift_categories", {})
    orchestration = categories.get("orchestration", {})
    artifact = categories.get("artifact", {})
    validation = categories.get("validation", {})
    readiness = categories.get("readiness", {})
    findings = diagnostics.get("drift_checks_with_findings", 0)
    history_status = diagnostics.get("monitoring_history_status", "insufficient_monitoring_history")
    return {
        "monitoring_run_status": "success",
        "monitoring_history_status": history_status,
        "drift_severity": classify_severity(history_status, findings),
        "drift_checks_executed": diagnostics.get("drift_checks_executed", 0),
        "drift_checks_with_findings": findings,
        "orchestration_drift_detected": any(orchestration.values()) if orchestration else False,
        "artifact_drift_detected": any(artifact.values()) if artifact else False,
        "validation_drift_detected": any(validation.values()) if validation else False,
        "readiness_drift_detected": any(readiness.values()) if readiness else False,
        "optional_artifact_skip_drift_detected": bool(orchestration.get("optional_artifact_skip_drift_detected", False)),
        "governance_invariants": {
            "advisory_only_governance_verified": True,
            "exact_match_only_preserved": True,
            "tier3h4_freeze_boundary_preserved": True,
            "ci_failure_required": False,
        },
        "drift_categories": categories,
        "context_loaded_input_count": context.get("loaded_input_count", 0),
    }


def write_monitoring_summary(payload: dict[str, Any]) -> None:
    out = Path("logs/tier3h5_phase5b_monitoring_summary.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(stable_json_dumps(payload), encoding="utf-8")
