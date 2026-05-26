"""LR6-EVID11 first real replay_richness payload builder (in-memory, evidence-only)."""
from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_evid6_minimal_in_memory_metrics_emission_hook import (
    emit_lr6_replay_metric_evidence,
)

TARGET_METRIC = "replay_richness"
DETERMINISTIC_VERSION = "LR6_EVID11_FIRST_REAL_REPLAY_RICHNESS_PAYLOAD_BUILDER_V1"

REQUIRED_COUNTS = [
    "replay_entity_count",
    "distinct_candidate_count",
    "distinct_role_count",
    "distinct_cluster_count",
]


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _extract_count_bucket(source_artifact: dict[str, Any]) -> dict[str, Any]:
    metrics = source_artifact.get("metrics")
    if isinstance(metrics, dict):
        metric_bucket = metrics.get(TARGET_METRIC)
        if isinstance(metric_bucket, dict):
            return metric_bucket
    direct_bucket = source_artifact.get(TARGET_METRIC)
    if isinstance(direct_bucket, dict):
        return direct_bucket
    return source_artifact


def build_lr6_evid11_builder_context() -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-EVID11",
        "metric_target": TARGET_METRIC,
        "scope": "first_real_replay_richness_payload_builder",
        "constraints": [
            "in_memory_only",
            "evidence_only",
            "no_persistence_write",
            "no_live_ingestion",
            "no_direct_sql",
            "no_prediction_or_trading",
            "single_metric_only",
        ],
    }


def extract_lr6_evid11_structured_richness_fields(source_artifact: dict[str, Any]) -> dict[str, Any]:
    artifact = source_artifact if isinstance(source_artifact, dict) else {}
    count_bucket = _extract_count_bucket(artifact)
    fields = {name: count_bucket.get(name) for name in REQUIRED_COUNTS}

    refs = artifact.get("source_artifact_refs")
    measurement_basis = artifact.get("measurement_basis", "narrative_only")
    scaffold_only = bool(artifact.get("scaffold_only", False))
    baseline_present = bool(artifact.get("baseline_reference_payload") or artifact.get("before_after_comparison"))

    return {
        **fields,
        "source_artifact_refs": refs if isinstance(refs, list) else [],
        "measurement_basis": measurement_basis,
        "scaffold_only": scaffold_only,
        "baseline_comparison_present": baseline_present,
        "narrative_text_present": isinstance(artifact.get("narrative"), str) and bool(artifact["narrative"].strip()),
    }


def validate_lr6_evid11_richness_source_artifact(source_artifact: dict[str, Any]) -> dict[str, Any]:
    extracted = extract_lr6_evid11_structured_richness_fields(source_artifact)
    invalid_reasons: list[str] = []
    valid_counts: dict[str, int] = {}

    for field in REQUIRED_COUNTS:
        value = extracted[field]
        if _is_non_negative_int(value):
            valid_counts[field] = value
        else:
            if value is None:
                invalid_reasons.append(f"missing_{field}")
            elif isinstance(value, bool) or not isinstance(value, int):
                invalid_reasons.append(f"non_integer_{field}")
            else:
                invalid_reasons.append(f"negative_{field}")

    basis = extracted["measurement_basis"]
    is_narrative_only = basis == "narrative_only"
    has_refs = len(extracted["source_artifact_refs"]) > 0

    status = "MEASURED"
    if extracted["scaffold_only"]:
        status = "SCAFFOLD_ONLY"
    elif is_narrative_only:
        status = "NOT_COMPARABLE"
    elif len(valid_counts) == 0:
        status = "NOT_COMPARABLE"
    elif len(valid_counts) < len(REQUIRED_COUNTS) or not has_refs:
        status = "PARTIAL"

    return {
        "metric_target": TARGET_METRIC,
        "valid_count_fields": valid_counts,
        "invalid_reasons": sorted(invalid_reasons),
        "measurement_basis": basis,
        "source_artifact_refs": extracted["source_artifact_refs"],
        "scaffold_only": extracted["scaffold_only"],
        "baseline_comparison_present": extracted["baseline_comparison_present"],
        "evidence_status": status,
    }


def build_lr6_evid11_replay_richness_payload(source_artifact: dict[str, Any]) -> dict[str, Any]:
    validation = validate_lr6_evid11_richness_source_artifact(source_artifact)
    counts = validation["valid_count_fields"]

    replay_entity_count = counts.get("replay_entity_count", 0)
    distinct_candidate_count = counts.get("distinct_candidate_count", 0)
    distinct_role_count = counts.get("distinct_role_count", 0)
    distinct_cluster_count = counts.get("distinct_cluster_count", 0)

    diversity_ratio = min(1.0, round((distinct_role_count + distinct_cluster_count) / max(replay_entity_count, 1), 6))
    richness_score = min(1.0, round((distinct_candidate_count + distinct_role_count + distinct_cluster_count) / max(replay_entity_count * 2, 1), 6))

    payload = {
        "metric_dimension": TARGET_METRIC,
        "replay_entity_count": replay_entity_count,
        "distinct_candidate_count": distinct_candidate_count,
        "distinct_role_count": distinct_role_count,
        "distinct_cluster_count": distinct_cluster_count,
        "source_artifact_refs": validation["source_artifact_refs"],
        "measurement_basis": validation["measurement_basis"],
        "scaffold_only": validation["scaffold_only"],
        "comparison_ready": bool(validation["evidence_status"] == "MEASURED" and validation["baseline_comparison_present"]),
        "evidence_status": validation["evidence_status"],
        "richness_score": richness_score,
        "diversity_ratio": diversity_ratio,
        "concentration_warning": diversity_ratio < 0.25,
    }

    return payload


def build_lr6_evid11_payload_validation_result(source_artifact: dict[str, Any]) -> dict[str, Any]:
    validation = validate_lr6_evid11_richness_source_artifact(source_artifact)
    payload = build_lr6_evid11_replay_richness_payload(source_artifact)
    return {
        "metric_target": TARGET_METRIC,
        "evidence_status": payload["evidence_status"],
        "valid_count_field_count": len(validation["valid_count_fields"]),
        "invalid_reasons": validation["invalid_reasons"],
        "comparison_ready": payload["comparison_ready"],
    }


def build_lr6_evid11_scaffold_rejection_result(source_artifact: dict[str, Any]) -> dict[str, Any]:
    payload = build_lr6_evid11_replay_richness_payload(source_artifact)
    rejected = payload["scaffold_only"] or payload["measurement_basis"] == "narrative_only"
    return {
        "metric_target": TARGET_METRIC,
        "rejected": rejected,
        "evidence_status": payload["evidence_status"],
        "reason": "scaffold_or_narrative_only" if rejected else "not_rejected",
    }


def build_lr6_evid11_evid6_emission_candidate(source_artifact: dict[str, Any]) -> dict[str, Any]:
    payload = build_lr6_evid11_replay_richness_payload(source_artifact)
    replay_payload = {
        "metrics": {
            TARGET_METRIC: {
                "replay_entity_count": payload["replay_entity_count"],
                "distinct_role_count": payload["distinct_role_count"],
                "distinct_cluster_count": payload["distinct_cluster_count"],
                "novel_bridge_count": 0,
                "richness_score": payload["richness_score"],
            }
        }
    }
    records = emit_lr6_replay_metric_evidence(
        replay_phase="BASELINE",
        wave_id="LR6_EVID11_IN_MEMORY_WAVE",
        candidate_scope_id="LR6_EVID11_SCOPE",
        candidate_count=payload["distinct_candidate_count"],
        timestamp_or_snapshot_label="LR6_EVID11_T0",
        replay_observation_payload=replay_payload,
        source_artifact="lr6_evid11_replay_richness_payload_builder",
        source_module="lr6_evid11_first_real_replay_richness_payload_builder",
    )
    replay_record = [r for r in records if r["metric_dimension"] == TARGET_METRIC][0]
    return {
        "metric_target": TARGET_METRIC,
        "input_payload": payload,
        "evid6_record": replay_record,
        "evid6_contract_compatible": True,
    }


def certify_lr6_evid11_builder_boundary() -> dict[str, Any]:
    return {
        "planning_only": False,
        "builder_only": True,
        "evidence_only": True,
        "in_memory_only": True,
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


def build_lr6_evid11_supervisor_review() -> dict[str, Any]:
    return {
        "objective": "Build first deterministic in-memory replay_richness payload builder from structured artifacts only.",
        "inspected_prior_evid9_evid10_design": [
            "lr6_evid9_real_replay_metric_payload_production_plan.py",
            "lr6_evid10_first_real_replay_metric_payload_emission_design.py",
            "lr6_evid6_minimal_in_memory_metrics_emission_hook.py",
        ],
        "structured_source_artifact_assumptions": [
            "required counts are structured integers >= 0",
            "source_artifact_refs carries explicit lineage references",
            "measurement_basis differentiates structured evidence from narrative_only",
        ],
        "payload_extraction_logic": extract_lr6_evid11_structured_richness_fields({}),
        "validation_logic": "missing/non-integer/negative counts downgrade status; scaffold_only and narrative_only cannot be MEASURED",
        "scaffold_narrative_rejection_logic": "scaffold_only=True or measurement_basis=narrative_only blocks MEASURED",
        "evid6_compatibility": "local deterministic mapping to EVID6 replay_richness required fields without hook contract changes",
        "sample_valid_in_memory_payload": build_lr6_evid11_replay_richness_payload({
            "replay_entity_count": 10,
            "distinct_candidate_count": 6,
            "distinct_role_count": 4,
            "distinct_cluster_count": 3,
            "source_artifact_refs": ["artifact://sample"],
            "measurement_basis": "observed_structured_fields",
        }),
        "sample_rejected_scaffold_payload": build_lr6_evid11_replay_richness_payload({
            "replay_entity_count": 10,
            "distinct_candidate_count": 6,
            "distinct_role_count": 4,
            "distinct_cluster_count": 3,
            "source_artifact_refs": ["artifact://sample"],
            "measurement_basis": "observed_structured_fields",
            "scaffold_only": True,
        }),
        "boundary_certification": certify_lr6_evid11_builder_boundary(),
        "recommendation_for_next_step": "Wire this builder to real replay observation artifact producers, then call EVID6 emission hook in-memory only.",
    }


def build_lr6_evid11_markdown_report() -> str:
    review = build_lr6_evid11_supervisor_review()
    return "\n".join([
        "# LR6-EVID11 First Real Replay Richness Payload Builder",
        "## objective",
        review["objective"],
        "## inspected prior EVID9/EVID10 design",
        str(review["inspected_prior_evid9_evid10_design"]),
        "## structured source artifact assumptions",
        str(review["structured_source_artifact_assumptions"]),
        "## payload extraction logic",
        str(review["payload_extraction_logic"]),
        "## validation logic",
        review["validation_logic"],
        "## scaffold/narrative rejection logic",
        review["scaffold_narrative_rejection_logic"],
        "## EVID6 compatibility",
        review["evid6_compatibility"],
        "## sample valid in-memory payload",
        str(review["sample_valid_in_memory_payload"]),
        "## sample rejected scaffold payload",
        str(review["sample_rejected_scaffold_payload"]),
        "## boundary certification",
        str(review["boundary_certification"]),
        "## recommendation for next step",
        review["recommendation_for_next_step"],
    ])


__all__ = [
    "build_lr6_evid11_builder_context",
    "extract_lr6_evid11_structured_richness_fields",
    "validate_lr6_evid11_richness_source_artifact",
    "build_lr6_evid11_replay_richness_payload",
    "build_lr6_evid11_evid6_emission_candidate",
    "build_lr6_evid11_payload_validation_result",
    "build_lr6_evid11_scaffold_rejection_result",
    "build_lr6_evid11_supervisor_review",
    "build_lr6_evid11_markdown_report",
    "certify_lr6_evid11_builder_boundary",
]
