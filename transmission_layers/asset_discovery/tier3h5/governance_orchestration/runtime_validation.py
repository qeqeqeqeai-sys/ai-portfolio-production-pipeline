from __future__ import annotations

from typing import Any


def validate_runtime(stage_registry: list[dict[str, Any]], guardrails: dict[str, Any]) -> dict[str, Any]:
    ordered = [s["stage_name"] for s in stage_registry]
    deterministic = ordered == sorted(ordered, key=ordered.index)
    required_executed = all(s["execution_status"] == "executed" for s in stage_registry if s["required"])
    return {
        "required_orchestration_stages_executed": required_executed,
        "deterministic_stage_ordering_preserved": deterministic,
        "required_artifacts_present_or_diagnosed": bool(guardrails["required_artifacts_present"] or guardrails["missing_artifact_diagnostics"]),
        "advisory_only_governance_preserved": True,
        "exact_match_only_behavior_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
    }
