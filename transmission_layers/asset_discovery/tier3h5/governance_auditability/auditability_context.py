from __future__ import annotations

import json
from pathlib import Path
from typing import Any

INPUTS: tuple[str, ...] = (
    "logs/tier3h5_orchestration_summary.json",
    "logs/tier3h5_orchestration_runtime_context.json",
    "logs/tier3h5_orchestration_guardrails.json",
    "logs/tier3h5_artifact_coordination_summary.json",
    "logs/tier3h5_upload_coordination_summary.json",
    "logs/tier3h5_phase5a_orchestration_summary.json",
    "logs/tier3h5_monitoring_context.json",
    "logs/tier3h5_governance_drift_diagnostics.json",
    "logs/tier3h5_orchestration_drift_summary.json",
    "logs/tier3h5_artifact_drift_summary.json",
    "logs/tier3h5_validation_drift_summary.json",
    "logs/tier3h5_readiness_drift_summary.json",
    "logs/tier3h5_phase5b_monitoring_summary.json",
    "logs/tier3h5_monitoring_history_context.json",
    "logs/tier3h5_governance_trend_analytics.json",
    "logs/tier3h5_drift_frequency_summary.json",
    "logs/tier3h5_orchestration_trend_summary.json",
    "logs/tier3h5_artifact_trend_summary.json",
    "logs/tier3h5_readiness_trend_summary.json",
    "logs/tier3h5_phase5c_history_summary.json",
    "logs/tier3h5_governance_reporting_context.json",
    "logs/tier3h5_operational_health_report.json",
    "logs/tier3h5_executive_readiness_summary.json",
    "logs/tier3h5_drift_operational_report.json",
    "logs/tier3h5_release_confidence_summary.json",
    "logs/tier3h5_dashboard_export_readiness.json",
    "logs/tier3h5_phase5d_reporting_summary.json",
)


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": "))


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: normalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return sorted((normalize(v) for v in value), key=stable_json_dumps)
    if isinstance(value, bool) or value is None:
        return value
    return value


def load_auditability_context() -> dict[str, Any]:
    context: dict[str, Any] = {"inputs": {}, "missing_inputs": []}
    for path in INPUTS:
        p = Path(path)
        if p.exists():
            context["inputs"][path] = normalize(json.loads(p.read_text(encoding="utf-8")))
        else:
            context["missing_inputs"].append(path)
    context["loaded_input_count"] = len(context["inputs"])
    context["missing_input_count"] = len(context["missing_inputs"])
    return context
