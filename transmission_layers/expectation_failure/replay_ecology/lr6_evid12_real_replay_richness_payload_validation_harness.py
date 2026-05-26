"""LR6-EVID12 deterministic in-memory validation harness for LR6-EVID11 replay_richness payloads."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_evid11_first_real_replay_richness_payload_builder import (
    build_lr6_evid11_replay_richness_payload,
)

DETERMINISTIC_VERSION = "LR6_EVID12_REAL_REPLAY_RICHNESS_PAYLOAD_VALIDATION_HARNESS_V1"
TARGET_METRIC = "replay_richness"


def build_lr6_evid12_validation_context() -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-EVID12",
        "metric_target": TARGET_METRIC,
        "scope": "real_replay_richness_payload_validation_harness",
        "validation_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "non_persistent": True,
    }


def build_lr6_evid12_validation_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "valid_structured_artifact",
            "input_class": "structured",
            "artifact": {
                "replay_entity_count": 12,
                "distinct_candidate_count": 8,
                "distinct_role_count": 5,
                "distinct_cluster_count": 4,
                "source_artifact_refs": ["artifact://valid-structured"],
                "measurement_basis": "structured_observation",
            },
            "expected_status": ["MEASURED"],
            "expected_measured_allowed": True,
            "expected_comparison_ready": False,
        },
        {
            "scenario_id": "partial_structured_artifact",
            "input_class": "partial",
            "artifact": {
                "replay_entity_count": 10,
                "distinct_candidate_count": 6,
                "source_artifact_refs": ["artifact://partial"],
                "measurement_basis": "structured_observation",
            },
            "expected_status": ["PARTIAL", "NOT_COMPARABLE"],
            "expected_measured_allowed": False,
            "expected_comparison_ready": False,
        },
        {
            "scenario_id": "scaffold_only_artifact",
            "input_class": "scaffold",
            "artifact": {
                "replay_entity_count": 10,
                "distinct_candidate_count": 6,
                "distinct_role_count": 3,
                "distinct_cluster_count": 2,
                "source_artifact_refs": ["artifact://scaffold"],
                "measurement_basis": "structured_observation",
                "scaffold_only": True,
            },
            "expected_status": ["SCAFFOLD_ONLY", "NOT_COMPARABLE"],
            "expected_measured_allowed": False,
            "expected_comparison_ready": False,
        },
        {
            "scenario_id": "narrative_only_artifact",
            "input_class": "narrative",
            "artifact": {
                "narrative": "Replay looked rich but only described in prose.",
                "measurement_basis": "narrative_only",
                "source_artifact_refs": ["artifact://narrative-only"],
            },
            "expected_status": ["NOT_COMPARABLE"],
            "expected_measured_allowed": False,
            "expected_comparison_ready": False,
        },
        {
            "scenario_id": "malformed_counts_artifact",
            "input_class": "malformed",
            "artifact": {
                "replay_entity_count": -1,
                "distinct_candidate_count": "8",
                "distinct_role_count": None,
                "distinct_cluster_count": 2.5,
                "source_artifact_refs": ["artifact://malformed"],
                "measurement_basis": "structured_observation",
            },
            "expected_status": ["NOT_COMPARABLE", "PARTIAL"],
            "expected_measured_allowed": False,
            "expected_comparison_ready": False,
        },
        {
            "scenario_id": "missing_lineage_artifact",
            "input_class": "missing_lineage",
            "artifact": {
                "replay_entity_count": 12,
                "distinct_candidate_count": 8,
                "distinct_role_count": 5,
                "distinct_cluster_count": 4,
                "measurement_basis": "structured_observation",
            },
            "expected_status": ["PARTIAL", "NOT_COMPARABLE"],
            "expected_measured_allowed": False,
            "expected_comparison_ready": False,
        },
        {
            "scenario_id": "dry_run_structured_artifact",
            "input_class": "dry_run",
            "artifact": {
                "replay_entity_count": 11,
                "distinct_candidate_count": 7,
                "distinct_role_count": 4,
                "distinct_cluster_count": 3,
                "source_artifact_refs": ["artifact://dry-run"],
                "measurement_basis": "structured_observation",
                "dry_run": True,
            },
            "expected_status": ["PARTIAL", "MEASURED"],
            "expected_measured_allowed": True,
            "expected_comparison_ready": False,
        },
        {
            "scenario_id": "baseline_comparison_artifact",
            "input_class": "baseline_present",
            "artifact": {
                "replay_entity_count": 12,
                "distinct_candidate_count": 9,
                "distinct_role_count": 6,
                "distinct_cluster_count": 4,
                "source_artifact_refs": ["artifact://baseline-present"],
                "measurement_basis": "structured_observation",
                "before_after_comparison": {"baseline": "T0", "enriched": "T1"},
            },
            "expected_status": ["MEASURED"],
            "expected_measured_allowed": True,
            "expected_comparison_ready": True,
        },
        {
            "scenario_id": "baseline_missing_artifact",
            "input_class": "baseline_missing",
            "artifact": {
                "replay_entity_count": 12,
                "distinct_candidate_count": 9,
                "distinct_role_count": 6,
                "distinct_cluster_count": 4,
                "source_artifact_refs": ["artifact://baseline-missing"],
                "measurement_basis": "structured_observation",
            },
            "expected_status": ["MEASURED"],
            "expected_measured_allowed": True,
            "expected_comparison_ready": False,
        },
    ]


def run_lr6_evid12_validation_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    payload = build_lr6_evid11_replay_richness_payload(deepcopy(scenario["artifact"]))
    observed_status = payload["evidence_status"]
    observed_measured_allowed = observed_status == "MEASURED"
    comparison_ready = bool(payload.get("comparison_ready", False))
    scaffold_only = bool(payload.get("scaffold_only", False))

    pass_status = observed_status in scenario["expected_status"]
    pass_measured = observed_measured_allowed == scenario["expected_measured_allowed"]
    pass_comparison = comparison_ready == scenario["expected_comparison_ready"]
    passed = pass_status and pass_measured and pass_comparison

    failure_reasons = []
    if not pass_status:
        failure_reasons.append(f"status_mismatch:{observed_status}")
    if not pass_measured:
        failure_reasons.append(f"measured_mismatch:{observed_measured_allowed}")
    if not pass_comparison:
        failure_reasons.append(f"comparison_mismatch:{comparison_ready}")

    safety_notes = []
    if scenario["input_class"] in {"scaffold", "narrative", "malformed", "missing_lineage"}:
        safety_notes.append("must_not_promote_to_measured")
    if scenario["scenario_id"] == "baseline_missing_artifact":
        safety_notes.append("must_not_be_comparison_ready")
    if scenario["scenario_id"] == "dry_run_structured_artifact":
        safety_notes.append("dry_run_caveat_recorded")

    return {
        "scenario_id": scenario["scenario_id"],
        "input_class": scenario["input_class"],
        "expected_status": scenario["expected_status"],
        "observed_status": observed_status,
        "expected_measured_allowed": scenario["expected_measured_allowed"],
        "observed_measured_allowed": observed_measured_allowed,
        "scaffold_only": scaffold_only,
        "comparison_ready": comparison_ready,
        "pass": passed,
        "failure_reason": ";".join(failure_reasons) if failure_reasons else "",
        "safety_notes": safety_notes,
        "dry_run_caveat": bool(scenario["artifact"].get("dry_run", False)),
    }


def _is_unsafe_promotion(row: dict[str, Any]) -> bool:
    if row["scenario_id"] in {
        "scaffold_only_artifact",
        "narrative_only_artifact",
        "malformed_counts_artifact",
        "missing_lineage_artifact",
    } and row["observed_status"] == "MEASURED":
        return True
    if row["scenario_id"] == "baseline_missing_artifact" and row["comparison_ready"]:
        return True
    return False


def run_lr6_evid12_validation_harness() -> dict[str, Any]:
    scenarios = build_lr6_evid12_validation_scenarios()
    results = [run_lr6_evid12_validation_scenario(s) for s in scenarios]

    summary = {
        "total_scenarios": len(results),
        "passed": sum(1 for r in results if r["pass"]),
        "failed": sum(1 for r in results if not r["pass"]),
        "measured_count": sum(1 for r in results if r["observed_status"] == "MEASURED"),
        "partial_count": sum(1 for r in results if r["observed_status"] == "PARTIAL"),
        "not_comparable_count": sum(1 for r in results if r["observed_status"] == "NOT_COMPARABLE"),
        "unsafe_promotion_count": sum(1 for r in results if _is_unsafe_promotion(r)),
        "comparison_ready_count": sum(1 for r in results if r["comparison_ready"]),
    }
    return {"context": build_lr6_evid12_validation_context(), "scenario_results": results, "aggregate_summary": summary}


def build_lr6_evid12_validation_matrix() -> list[dict[str, Any]]:
    return run_lr6_evid12_validation_harness()["scenario_results"]


def build_lr6_evid12_status_transition_review() -> dict[str, Any]:
    by_id = {r["scenario_id"]: r for r in build_lr6_evid12_validation_matrix()}
    return {
        "structured_to_measured": by_id["valid_structured_artifact"]["observed_status"],
        "partial_to_partial_or_not_comparable": by_id["partial_structured_artifact"]["observed_status"],
        "scaffold_to_scaffold_only_or_not_comparable": by_id["scaffold_only_artifact"]["observed_status"],
        "narrative_to_not_comparable": by_id["narrative_only_artifact"]["observed_status"],
        "malformed_to_not_comparable": by_id["malformed_counts_artifact"]["observed_status"],
        "missing_lineage_to_partial_or_not_comparable": by_id["missing_lineage_artifact"]["observed_status"],
        "baseline_present_comparison_ready": by_id["baseline_comparison_artifact"]["comparison_ready"],
    }


def build_lr6_evid12_rejection_safety_review() -> dict[str, Any]:
    harness = run_lr6_evid12_validation_harness()
    return {
        "unsafe_promotion_count": harness["aggregate_summary"]["unsafe_promotion_count"],
        "unsafe_promotion_scenarios": [r["scenario_id"] for r in harness["scenario_results"] if _is_unsafe_promotion(r)],
    }


def build_lr6_evid12_comparison_readiness_review() -> dict[str, Any]:
    matrix = build_lr6_evid12_validation_matrix()
    return {
        "comparison_ready_scenarios": [r["scenario_id"] for r in matrix if r["comparison_ready"]],
        "baseline_missing_comparison_ready": next(r["comparison_ready"] for r in matrix if r["scenario_id"] == "baseline_missing_artifact"),
    }


def certify_lr6_evid12_validation_boundary() -> dict[str, Any]:
    return {
        "validation_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": TARGET_METRIC,
        "all_seven_metrics_implemented": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "no_interpretation_claims": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_evid12_supervisor_review() -> dict[str, Any]:
    harness = run_lr6_evid12_validation_harness()
    return {
        "objective": "Validate LR6-EVID11 replay_richness payload behavior against realistic artifact shapes.",
        "inspected_evid11_builder": "lr6_evid11_first_real_replay_richness_payload_builder.py",
        "validation_scenario_matrix": harness["scenario_results"],
        "status_transition_review": build_lr6_evid12_status_transition_review(),
        "rejection_safety_review": build_lr6_evid12_rejection_safety_review(),
        "comparison_readiness_review": build_lr6_evid12_comparison_readiness_review(),
        "aggregate_validation_result": harness["aggregate_summary"],
        "unsafe_promotion_review": build_lr6_evid12_rejection_safety_review(),
        "boundary_certification": certify_lr6_evid12_validation_boundary(),
        "recommendation_for_next_step": "Keep replay_richness validation in-memory; wire to governed execution only after explicit approval.",
    }


def build_lr6_evid12_markdown_report() -> str:
    review = build_lr6_evid12_supervisor_review()
    return "\n".join([
        "# LR6-EVID12 Real Replay Richness Payload Validation Harness",
        "## objective",
        str(review["objective"]),
        "## inspected EVID11 builder",
        str(review["inspected_evid11_builder"]),
        "## validation scenario matrix",
        str(review["validation_scenario_matrix"]),
        "## status transition review",
        str(review["status_transition_review"]),
        "## rejection safety review",
        str(review["rejection_safety_review"]),
        "## comparison readiness review",
        str(review["comparison_readiness_review"]),
        "## aggregate validation result",
        str(review["aggregate_validation_result"]),
        "## unsafe promotion review",
        str(review["unsafe_promotion_review"]),
        "## boundary certification",
        str(review["boundary_certification"]),
        "## recommendation for next step",
        str(review["recommendation_for_next_step"]),
    ])


__all__ = [
    "build_lr6_evid12_validation_context",
    "build_lr6_evid12_validation_scenarios",
    "run_lr6_evid12_validation_scenario",
    "run_lr6_evid12_validation_harness",
    "build_lr6_evid12_validation_matrix",
    "build_lr6_evid12_status_transition_review",
    "build_lr6_evid12_rejection_safety_review",
    "build_lr6_evid12_comparison_readiness_review",
    "build_lr6_evid12_supervisor_review",
    "build_lr6_evid12_markdown_report",
    "certify_lr6_evid12_validation_boundary",
]
