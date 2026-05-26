"""LR6-EVID14 supervisor meaningfulness review for first dry-run replay_richness payloads."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

DETERMINISTIC_VERSION = "LR6_EVID14_FIRST_REPLAY_RICHNESS_PAYLOAD_SUPERVISOR_REVIEW_V1"
TARGET_METRIC = "replay_richness"


def build_lr6_evid14_review_context() -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-EVID14",
        "metric_target": TARGET_METRIC,
        "scope": "first_replay_richness_payload_meaningfulness_supervisor_review",
        "review_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "non_persistent": True,
        "non_ingestion": True,
    }


def build_lr6_evid14_payload_meaningfulness_criteria() -> dict[str, str]:
    return {
        "has_valid_measured_status": "Payload evidence_status is MEASURED.",
        "has_structured_lineage": "source_artifact_refs exists and is non-empty.",
        "has_nonzero_entity_count": "replay_entity_count is integer > 0.",
        "has_role_diversity": "distinct_role_count is integer >= 2.",
        "has_cluster_diversity": "distinct_cluster_count is integer >= 2.",
        "has_nontrivial_diversity_ratio": "diversity ratio (distinct_candidate_count/replay_entity_count) >= 0.30.",
        "concentration_warning_absent_or_explained": "No concentration_warning, or explanation exists.",
        "comparison_ready_supported": "comparison_ready is true.",
        "dry_run_caveat_present": "dry_run_caveat text is present for dry-run safety framing.",
        "no_scaffold_or_narrative_promotion": "scaffold_only is false and measurement_basis is not narrative_only.",
        "sufficient_for_persistence_consideration": "All signal criteria pass except optional comparison readiness.",
        "sufficient_for_live_ingestion_consideration": "Would require stronger conditions; intentionally false at this phase.",
    }


def _safe_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    return value if isinstance(value, int) else None


def review_lr6_evid14_replay_richness_payload(payload: dict[str, Any]) -> dict[str, Any]:
    src = deepcopy(payload if isinstance(payload, dict) else {})
    entity = _safe_int(src, "replay_entity_count")
    cand = _safe_int(src, "distinct_candidate_count")
    role = _safe_int(src, "distinct_role_count")
    cluster = _safe_int(src, "distinct_cluster_count")
    refs = src.get("source_artifact_refs") if isinstance(src.get("source_artifact_refs"), list) else []
    warning = src.get("concentration_warning")
    comparison_ready = bool(src.get("comparison_ready", False))
    dry_run_caveat = src.get("dry_run_caveat")

    diversity_ratio = (cand / entity) if isinstance(cand, int) and isinstance(entity, int) and entity > 0 else 0.0

    checks = {
        "has_valid_measured_status": src.get("evidence_status") == "MEASURED",
        "has_structured_lineage": len(refs) > 0,
        "has_nonzero_entity_count": isinstance(entity, int) and entity > 0,
        "has_role_diversity": isinstance(role, int) and role >= 2,
        "has_cluster_diversity": isinstance(cluster, int) and cluster >= 2,
        "has_nontrivial_diversity_ratio": diversity_ratio >= 0.30,
        "concentration_warning_absent_or_explained": (not warning) or bool(src.get("concentration_warning_explained", False)),
        "comparison_ready_supported": comparison_ready,
        "dry_run_caveat_present": isinstance(dry_run_caveat, str) and len(dry_run_caveat.strip()) > 0,
        "no_scaffold_or_narrative_promotion": not bool(src.get("scaffold_only", False)) and src.get("measurement_basis") != "narrative_only",
    }

    if not checks["has_valid_measured_status"] or not checks["no_scaffold_or_narrative_promotion"]:
        classification = "unsafe_or_not_measured"
    elif not checks["has_structured_lineage"]:
        classification = "insufficient_lineage"
    elif not (checks["has_role_diversity"] and checks["has_cluster_diversity"] and checks["has_nontrivial_diversity_ratio"]):
        classification = "insufficient_diversity"
    elif not checks["comparison_ready_supported"]:
        classification = "comparison_not_ready"
    elif all(checks.values()):
        classification = "meaningful_candidate"
    else:
        classification = "mechanically_valid_but_shallow"

    if classification == "insufficient_diversity" and checks["has_valid_measured_status"]:
        classification = "mechanically_valid_but_shallow"

    sufficient_for_persistence = checks["has_valid_measured_status"] and checks["has_structured_lineage"] and checks["has_nonzero_entity_count"] and checks["has_role_diversity"] and checks["has_cluster_diversity"] and checks["has_nontrivial_diversity_ratio"] and checks["concentration_warning_absent_or_explained"] and checks["dry_run_caveat_present"]

    return {
        "classification": classification,
        "criteria_checks": checks,
        "diversity_ratio": round(diversity_ratio, 4),
        "sufficient_for_persistence_consideration": sufficient_for_persistence,
        "sufficient_for_live_ingestion_consideration": False,
    }


def build_lr6_evid14_signal_sufficiency_review(reviews: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sufficient = [k for k, v in reviews.items() if v["sufficient_for_persistence_consideration"]]
    return {"sufficient_payload_ids": sufficient, "sufficient_count": len(sufficient), "total_reviewed": len(reviews)}


def build_lr6_evid14_payload_shallowness_review(reviews: dict[str, dict[str, Any]]) -> dict[str, Any]:
    shallow = [k for k, v in reviews.items() if v["classification"] in {"mechanically_valid_but_shallow", "comparison_not_ready"}]
    return {"shallow_payload_ids": shallow, "shallow_count": len(shallow)}


def build_lr6_evid14_persistence_readiness_review(reviews: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if any(v["classification"] == "meaningful_candidate" for v in reviews.values()):
        status = "conditionally_ready_for_limited_non_persistent_observation"
    else:
        status = "not_ready"
    return {"persistence_readiness": status, "persistence_authorized": False, "write_authorized": False}


def build_lr6_evid14_live_ingestion_readiness_review(reviews: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "live_ingestion_readiness": "not_ready",
        "live_ingestion_authorized": False,
        "rationale": "LR6-EVID14 is review-only evidence; no ingestion path is permitted.",
    }


def build_lr6_evid14_governed_emission_recommendation() -> dict[str, Any]:
    return {
        "governed_emission_recommendation": "Do not authorize writes; continue dry-run non-persistent observation and strengthen comparison readiness evidence.",
        "governed_activation_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "authorizes_writes": False,
    }


def certify_lr6_evid14_review_boundary() -> dict[str, Any]:
    return {
        "review_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": "replay_richness",
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


def build_lr6_evid14_supervisor_review() -> dict[str, Any]:
    samples = {
        "meaningful_measured_payload": {
            "evidence_status": "MEASURED", "replay_entity_count": 12, "distinct_candidate_count": 8,
            "distinct_role_count": 4, "distinct_cluster_count": 3, "source_artifact_refs": ["artifact://obs7/meaningful"],
            "measurement_basis": "structured_observation", "comparison_ready": True,
            "dry_run_caveat": "Preview-only attachment; no persistence.",
        },
        "shallow_measured_payload": {
            "evidence_status": "MEASURED", "replay_entity_count": 12, "distinct_candidate_count": 2,
            "distinct_role_count": 1, "distinct_cluster_count": 1, "source_artifact_refs": ["artifact://obs7/shallow"],
            "measurement_basis": "structured_observation", "comparison_ready": True,
            "concentration_warning": "high", "dry_run_caveat": "Preview-only attachment; no persistence.",
        },
        "scaffold_rejected_payload": {
            "evidence_status": "SCAFFOLD_ONLY", "scaffold_only": True, "measurement_basis": "narrative_only",
            "dry_run_caveat": "Preview-only attachment; no persistence.",
        },
        "missing_lineage_payload": {
            "evidence_status": "MEASURED", "replay_entity_count": 9, "distinct_candidate_count": 5,
            "distinct_role_count": 3, "distinct_cluster_count": 2, "measurement_basis": "structured_observation",
            "comparison_ready": True, "dry_run_caveat": "Preview-only attachment; no persistence.",
        },
        "comparison_not_ready_payload": {
            "evidence_status": "MEASURED", "replay_entity_count": 10, "distinct_candidate_count": 6,
            "distinct_role_count": 3, "distinct_cluster_count": 3, "source_artifact_refs": ["artifact://obs7/no-baseline"],
            "measurement_basis": "structured_observation", "comparison_ready": False,
            "dry_run_caveat": "Preview-only attachment; no persistence.",
        },
    }
    reviewed = {k: review_lr6_evid14_replay_richness_payload(v) for k, v in samples.items()}
    return {
        "objective": "Determine whether first dry-run replay_richness payloads are meaningfully useful or only mechanically valid.",
        "inspected_evid11_evid12_evid13_path": [
            "lr6_evid11_first_real_replay_richness_payload_builder.py",
            "lr6_evid12_real_replay_richness_payload_validation_harness.py",
            "lr6_evid13_dry_run_replay_richness_payload_attachment.py",
        ],
        "context": build_lr6_evid14_review_context(),
        "supervisor_meaningfulness_criteria": build_lr6_evid14_payload_meaningfulness_criteria(),
        "reviewed_sample_payloads": samples,
        "reviewed_sample_results": reviewed,
        "signal_sufficiency_review": build_lr6_evid14_signal_sufficiency_review(reviewed),
        "payload_shallowness_review": build_lr6_evid14_payload_shallowness_review(reviewed),
        "persistence_readiness_review": build_lr6_evid14_persistence_readiness_review(reviewed),
        "live_ingestion_readiness_review": build_lr6_evid14_live_ingestion_readiness_review(reviewed),
        "governed_emission_recommendation": build_lr6_evid14_governed_emission_recommendation(),
        "boundary_certification": certify_lr6_evid14_review_boundary(),
    }


def build_lr6_evid14_markdown_report() -> str:
    review = build_lr6_evid14_supervisor_review()
    lines = [
        "# LR6-EVID14 — First Replay Richness Payload Supervisor Review",
        "",
        "## objective",
        f"- {review['objective']}",
        "",
        "## inspected EVID11/EVID12/EVID13 path",
    ]
    lines.extend([f"- {x}" for x in review["inspected_evid11_evid12_evid13_path"]])
    lines.extend([
        "",
        "## supervisor meaningfulness criteria",
        f"- {review['supervisor_meaningfulness_criteria']}",
        "",
        "## reviewed sample payloads",
        f"- {list(review['reviewed_sample_payloads'].keys())}",
        "",
        "## signal sufficiency review",
        f"- {review['signal_sufficiency_review']}",
        "",
        "## payload shallowness review",
        f"- {review['payload_shallowness_review']}",
        "",
        "## persistence readiness review",
        f"- {review['persistence_readiness_review']}",
        "",
        "## live ingestion readiness review",
        f"- {review['live_ingestion_readiness_review']}",
        "",
        "## governed emission recommendation",
        f"- {review['governed_emission_recommendation']}",
        "",
        "## boundary certification",
        f"- {review['boundary_certification']}",
        "",
        "## recommendation for next step",
        "- Keep LR6-EVID14 in review-only mode and collect more comparison-ready dry-run evidence before any persistence consideration.",
    ])
    return "\n".join(lines)
