"""LR6-EVID10 first real replay metric payload emission design (planning-only, design-only)."""
from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_evid6_minimal_in_memory_metrics_emission_hook import (
    build_lr6_evid6_required_field_contract,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_evid9_real_replay_metric_payload_production_plan import (
    build_lr6_evid9_existing_observation_field_inventory,
    build_lr6_evid9_metric_computability_review,
    build_lr6_evid9_priority_metric_emission_order,
)

TARGET_METRIC = "replay_richness"
DESIGN_VERSION = "LR6_EVID10_FIRST_REAL_REPLAY_METRIC_PAYLOAD_EMISSION_DESIGN_V1"


def build_lr6_evid10_design_context() -> dict[str, Any]:
    return {
        "design_version": DESIGN_VERSION,
        "objective": "design first real non-synthetic EVID6-compatible replay metric payload emission path",
        "design_scope": "planning_only_design_only",
        "target_metric": TARGET_METRIC,
        "constraints": [
            "no_replay_execution",
            "no_live_ingestion",
            "no_persistence_write",
            "no_governed_activation",
            "no_direct_sql",
            "no_prediction_or_trading_logic",
            "no_new_interpretation_layer",
            "single_metric_only",
        ],
    }


def identify_lr6_evid10_first_metric_target() -> dict[str, Any]:
    priority_order = build_lr6_evid9_priority_metric_emission_order()
    computability = build_lr6_evid9_metric_computability_review()
    replay_richness_review = next(x for x in computability if x["metric_dimension"] == TARGET_METRIC)
    return {
        "selected_metric": TARGET_METRIC,
        "selected_metric_rank": priority_order.index(TARGET_METRIC) + 1,
        "selection_reason": "classified as easiest already-computable metric from structured replay observation fields",
        "evid9_computability": replay_richness_review["computability"],
        "all_seven_metrics_implemented": False,
    }


def build_lr6_evid10_replay_richness_payload_contract() -> dict[str, Any]:
    existing = set(build_lr6_evid9_existing_observation_field_inventory())
    required_counts = [
        "replay_entity_count",
        "distinct_candidate_count",
        "distinct_role_count",
        "distinct_cluster_count",
    ]
    optional_structured = {
        "distinct_theme_count": "narrative_only",
        "distinct_propagation_route_count": "narrative_only",
    }
    return {
        "metric_dimension": TARGET_METRIC,
        "required_identifiers": ["replay_phase", "wave_id", "candidate_scope_id", "candidate_count", "timestamp_or_snapshot_label"],
        "required_structured_count_fields": required_counts,
        "derived_fields": ["diversity_ratio", "concentration_warning"],
        "required_lineage_fields": ["source_artifact_refs", "measurement_basis"],
        "scaffold_only_logic": "False only when required_structured_count_fields are present as observed structured values and source_artifact_refs include at least one structured artifact",
        "measurement_readiness": {
            "measured_requires": [
                "all required_structured_count_fields are integers >= 0",
                "at least one structured source artifact reference",
                "measurement_basis != narrative_only",
            ],
            "disallowed": [
                "prose_inference_for_counts",
                "scaffold_only_payload_promoted_to_measured",
            ],
        },
        "field_availability_review": {
            "available_in_evid9_inventory": sorted([f for f in required_counts if f in existing]),
            "not_in_evid9_inventory": sorted([f for f in required_counts if f not in existing]),
            "optional_field_classification": {
                k: {
                    "availability": v,
                    "not_measurement_ready": True,
                    "excluded_from_first_payload": True,
                }
                for k, v in optional_structured.items()
            },
        },
    }


def build_lr6_evid10_existing_field_mapping() -> dict[str, Any]:
    return {
        "replay_entity_count": {"source_field": "replay_entity_count", "mapping_status": "direct_structured"},
        "distinct_role_count": {"source_field": "distinct_role_count", "mapping_status": "direct_structured"},
        "distinct_cluster_count": {"source_field": "distinct_cluster_count", "mapping_status": "direct_structured"},
        "distinct_candidate_count": {
            "source_field": "candidate_metadata distinct ids OR replay_observation_payload.distinct_candidate_count",
            "mapping_status": "conditionally_structured",
            "must_not_use": "narrative text inference",
        },
        "diversity_ratio": {
            "formula": "(distinct_role_count + distinct_cluster_count) / max(replay_entity_count, 1)",
            "bounded_to": "[0,1]",
            "mapping_status": "derived_from_structured_counts",
        },
        "concentration_warning": {
            "formula": "True when diversity_ratio < 0.25 else False",
            "mapping_status": "deterministic_derived_flag",
        },
        "source_artifact_refs": {
            "source_field": "artifact lineage references from replay observation producers",
            "mapping_status": "required_structured_lineage",
        },
        "measurement_basis": {
            "allowed_values": ["observed_structured_fields", "dry_run_derived_structured_fields", "narrative_only"],
            "mapping_status": "required_classification",
        },
    }


def build_lr6_evid10_payload_derivation_plan() -> list[dict[str, Any]]:
    return [
        {"step": 1, "action": "extract replay_richness candidate bucket from replay observation payload", "mode": "design_only"},
        {"step": 2, "action": "read required structured count fields and reject prose-only sources", "mode": "design_only"},
        {"step": 3, "action": "compute diversity_ratio and concentration_warning from validated counts", "mode": "design_only"},
        {"step": 4, "action": "attach source_artifact_refs and measurement_basis lineage", "mode": "design_only"},
        {"step": 5, "action": "map into EVID6 metric bucket for replay_richness without hook contract changes", "mode": "design_only"},
    ]


def build_lr6_evid10_evid6_compatibility_mapping() -> dict[str, Any]:
    evid6_contract = build_lr6_evid6_required_field_contract()[TARGET_METRIC]
    return {
        "metric_dimension": TARGET_METRIC,
        "evid6_required_fields": evid6_contract,
        "compatibility": {
            "replay_entity_count": "direct",
            "distinct_role_count": "direct",
            "distinct_cluster_count": "direct",
            "novel_bridge_count": "default 0 when absent; not inferred from prose",
            "richness_score": "use diversity_ratio when in [0,1] else 0",
        },
        "evidence_status_logic": {
            "MEASURED": "all EVID6 required fields valid and scaffold_only=False",
            "PARTIAL": "some valid fields present but not full EVID6 contract",
            "SCAFFOLD_ONLY": "scaffold markers present and no measurable structured fields",
        },
        "comparison_ready_logic": "False unless measured and baseline/before-after identifiers are present",
        "no_hook_contract_change_required": True,
    }


def build_lr6_evid10_validation_plan() -> dict[str, Any]:
    return {
        "deterministic_rules": [
            "required count fields must be integers >= 0",
            "at least one real structured source artifact must be present",
            "candidate/entity count cannot be inferred from prose",
            "scaffold-only input cannot become MEASURED",
            "dry-run-only simulation cannot become MEASURED unless it contains real structured observation fields and is clearly marked as dry-run-derived",
            "comparison_ready must be False unless before/after or baseline comparison fields exist",
        ],
        "failure_modes": [
            "missing_required_count_field",
            "non_integer_count_field",
            "narrative_only_measurement_basis",
            "missing_source_artifact_refs",
            "scaffold_promoted_to_measured",
        ],
    }


def build_lr6_evid10_non_synthetic_readiness_review() -> dict[str, Any]:
    return {
        "target_metric": TARGET_METRIC,
        "non_synthetic_ready_when": [
            "required structured counts are present and validated",
            "measurement_basis is observed_structured_fields or dry_run_derived_structured_fields",
            "source artifact lineage is explicit",
        ],
        "excluded_from_measured": [
            "narrative_only fields",
            "scaffold-only payloads",
            "dry-run payloads without structured count evidence",
        ],
    }


def build_lr6_evid10_integration_boundary_plan() -> dict[str, Any]:
    return {
        "integration_points": [
            "replay observation artifact builder emits structured replay_richness fields",
            "replay ecology dashboard payload builder preserves structured count fields",
            "lr6_evid6_minimal_in_memory_metrics_emission_hook.emit_lr6_replay_metric_evidence consumes mapped replay_richness bucket",
        ],
        "explicit_non_goals": [
            "no replay execution",
            "no persistence writes",
            "no governance activation",
            "no SQL",
            "no prediction/trading",
        ],
    }


def certify_lr6_evid10_design_boundary() -> dict[str, Any]:
    return {
        "planning_only": True,
        "design_only": True,
        "evidence_only": True,
        "execution_authorized": False,
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


def build_lr6_evid10_supervisor_review() -> dict[str, Any]:
    return {
        "objective": build_lr6_evid10_design_context()["objective"],
        "why_replay_richness_is_first": identify_lr6_evid10_first_metric_target(),
        "inspected_evid9_findings": build_lr6_evid9_metric_computability_review(),
        "inspected_replay_observation_structures": build_lr6_evid10_existing_field_mapping(),
        "first_real_payload_contract": build_lr6_evid10_replay_richness_payload_contract(),
        "excluded_narrative_scaffold_fields": build_lr6_evid10_replay_richness_payload_contract()["field_availability_review"]["optional_field_classification"],
        "evid6_compatibility_mapping": build_lr6_evid10_evid6_compatibility_mapping(),
        "payload_derivation_plan": build_lr6_evid10_payload_derivation_plan(),
        "validation_plan": build_lr6_evid10_validation_plan(),
        "non_synthetic_readiness_review": build_lr6_evid10_non_synthetic_readiness_review(),
        "integration_boundary_plan": build_lr6_evid10_integration_boundary_plan(),
        "boundary_certification": certify_lr6_evid10_design_boundary(),
        "recommendation_for_next_step": "Wire validated structured replay_richness fields at artifact production boundary and emit through existing EVID6 hook.",
    }


def build_lr6_evid10_markdown_report() -> str:
    review = build_lr6_evid10_supervisor_review()
    return "\n".join([
        "# LR6-EVID10 First Real Replay Metric Payload Emission Design",
        "## objective",
        review["objective"],
        "## why replay_richness is first",
        str(review["why_replay_richness_is_first"]),
        "## inspected EVID9 findings",
        str(review["inspected_evid9_findings"]),
        "## inspected replay observation structures",
        str(review["inspected_replay_observation_structures"]),
        "## first real payload contract",
        str(review["first_real_payload_contract"]),
        "## existing field mapping",
        str(build_lr6_evid10_existing_field_mapping()),
        "## excluded narrative/scaffold-only fields",
        str(review["excluded_narrative_scaffold_fields"]),
        "## EVID6 compatibility mapping",
        str(review["evid6_compatibility_mapping"]),
        "## payload derivation plan",
        str(review["payload_derivation_plan"]),
        "## validation plan",
        str(review["validation_plan"]),
        "## non-synthetic readiness review",
        str(review["non_synthetic_readiness_review"]),
        "## integration boundary plan",
        str(review["integration_boundary_plan"]),
        "## boundary certification",
        str(review["boundary_certification"]),
        "## recommendation for next step",
        review["recommendation_for_next_step"],
    ])


__all__ = [
    "build_lr6_evid10_design_context",
    "identify_lr6_evid10_first_metric_target",
    "build_lr6_evid10_replay_richness_payload_contract",
    "build_lr6_evid10_existing_field_mapping",
    "build_lr6_evid10_payload_derivation_plan",
    "build_lr6_evid10_evid6_compatibility_mapping",
    "build_lr6_evid10_validation_plan",
    "build_lr6_evid10_non_synthetic_readiness_review",
    "build_lr6_evid10_integration_boundary_plan",
    "build_lr6_evid10_supervisor_review",
    "build_lr6_evid10_markdown_report",
    "certify_lr6_evid10_design_boundary",
]
