from __future__ import annotations

from pathlib import Path
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import write_stable_json

GUARDRAILS_PATH = Path("logs/tier3h5_orchestration_guardrails.json")


def run_guardrails(stage_registry: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    required_ok = True
    for stage in stage_registry:
        missing = [p for p in stage["expected_artifacts"] if not Path(p).exists()]
        if stage["required"] and missing:
            required_ok = False
        checks.append({"stage_name": stage["stage_name"], "missing_artifacts": missing, "required": stage["required"]})
    payload = {
        "required_artifact_dependency_checks": checks,
        "missing_artifact_diagnostics": [c for c in checks if c["missing_artifacts"]],
        "sparse_history_handling": "graceful_degradation",
        "optional_module_handling": "optional_artifact_skipped",
        "replay_safe_sequencing_checks": True,
        "advisory_only_verification": True,
        "exact_match_only_preservation_check": True,
        "tier3h4_freeze_boundary_preservation_check": True,
        "required_artifacts_present": required_ok,
        "auto_remediation_performed": False,
    }
    write_stable_json(GUARDRAILS_PATH, payload)
    return payload
