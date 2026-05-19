from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PHASE_INPUTS: dict[str, tuple[str, ...]] = {
    "phase5a": (
        "logs/tier3h5_orchestration_summary.json",
        "logs/tier3h5_orchestration_runtime_context.json",
        "logs/tier3h5_orchestration_guardrails.json",
        "logs/tier3h5_artifact_coordination_summary.json",
        "logs/tier3h5_upload_coordination_summary.json",
        "logs/tier3h5_phase5a_orchestration_summary.json",
    ),
    "phase5b": (
        "logs/tier3h5_monitoring_context.json",
        "logs/tier3h5_governance_drift_diagnostics.json",
        "logs/tier3h5_orchestration_drift_summary.json",
        "logs/tier3h5_artifact_drift_summary.json",
        "logs/tier3h5_validation_drift_summary.json",
        "logs/tier3h5_readiness_drift_summary.json",
        "logs/tier3h5_phase5b_monitoring_summary.json",
    ),
    "phase5c": (
        "logs/tier3h5_monitoring_history_context.json",
        "logs/tier3h5_governance_trend_analytics.json",
        "logs/tier3h5_drift_frequency_summary.json",
        "logs/tier3h5_orchestration_trend_summary.json",
        "logs/tier3h5_artifact_trend_summary.json",
        "logs/tier3h5_readiness_trend_summary.json",
        "logs/tier3h5_phase5c_history_summary.json",
    ),
    "phase5d": (
        "logs/tier3h5_governance_reporting_context.json",
        "logs/tier3h5_operational_health_report.json",
        "logs/tier3h5_executive_readiness_summary.json",
        "logs/tier3h5_drift_operational_report.json",
        "logs/tier3h5_release_confidence_summary.json",
        "logs/tier3h5_dashboard_export_readiness.json",
        "logs/tier3h5_phase5d_reporting_summary.json",
    ),
    "phase5e": (
        "logs/tier3h5_auditability_context.json",
        "logs/tier3h5_governance_lineage_manifest.json",
        "logs/tier3h5_evidence_inventory.json",
        "logs/tier3h5_artifact_provenance_summary.json",
        "logs/tier3h5_monitoring_lineage_summary.json",
        "logs/tier3h5_reporting_lineage_summary.json",
        "logs/tier3h5_release_audit_snapshot.json",
        "logs/tier3h5_phase5e_auditability_summary.json",
    ),
}

def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": "))

def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: normalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return sorted((normalize(v) for v in value), key=stable_json_dumps)
    if value is None or isinstance(value, bool):
        return value
    return value

def load_control_plane_context() -> dict[str, Any]:
    inputs: dict[str, Any] = {}
    missing: list[str] = []
    phase_coverage: dict[str, bool] = {}
    artifact_coverage: dict[str, bool] = {}

    for phase, paths in PHASE_INPUTS.items():
        found = 0
        for path in paths:
            p = Path(path)
            exists = p.exists()
            artifact_coverage[path] = exists
            if exists:
                found += 1
                inputs[path] = normalize(json.loads(p.read_text(encoding="utf-8")))
            else:
                missing.append(path)
        phase_coverage[phase] = found > 0
    return {
        "inputs": inputs,
        "missing_inputs": sorted(missing),
        "phase_coverage": phase_coverage,
        "artifact_coverage": artifact_coverage,
        "loaded_input_count": len(inputs),
        "missing_input_count": len(missing),
    }
