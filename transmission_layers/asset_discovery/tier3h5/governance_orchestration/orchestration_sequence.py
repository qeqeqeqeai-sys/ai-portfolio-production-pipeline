from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StageSpec:
    stage_name: str
    required: bool
    optional: bool
    expected_artifacts: tuple[str, ...]


STAGE_REGISTRY: tuple[StageSpec, ...] = (
    StageSpec("governance_history", True, False, ("logs/tier3h5_phase4c_governance_history_summary.json",)),
    StageSpec("governance_continuity_analytics", True, False, ("logs/tier3h5_governance_continuity_history.json",)),
    StageSpec("governance_trend_analytics", True, False, ("logs/tier3h5_governance_trend_history.json",)),
    StageSpec("dashboard_readiness_generation", True, False, ("logs/tier3h5_dashboard_governance_summary.json",)),
    StageSpec("bi_export_generation", True, False, ("logs/tier3h5_phase4e_bi_export_summary.json",)),
    StageSpec("semantic_layer_export_generation", False, True, ("logs/tier3h5_bi_semantic_layer.json",)),
    StageSpec("governance_validation", False, True, ("logs/tier3h5_phase4f_operational_validation_summary.json",)),
    StageSpec("artifact_smoke_testing", False, True, ("logs/tier3h5_bi_artifact_inventory.json",)),
    StageSpec("operational_readiness_summaries", False, True, ("logs/tier3h5_phase4g_operational_readiness_summary.json",)),
)


def deterministic_stage_registry() -> list[dict[str, object]]:
    return [
        {
            "stage_name": s.stage_name,
            "required": s.required,
            "optional": s.optional,
            "expected_artifacts": list(s.expected_artifacts),
            "execution_status": "pending",
            "degradation_status": "none",
            "guardrail_status": "pending",
        }
        for s in STAGE_REGISTRY
    ]
