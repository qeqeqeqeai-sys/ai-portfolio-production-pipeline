"""LR6-EVID13 dry-run replay_richness payload attachment (in-memory, attachment-only)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_evid11_first_real_replay_richness_payload_builder import (
    build_lr6_evid11_evid6_emission_candidate,
    build_lr6_evid11_replay_richness_payload,
)

TARGET_METRIC = "replay_richness"
DETERMINISTIC_VERSION = "LR6_EVID13_DRY_RUN_REPLAY_RICHNESS_PAYLOAD_ATTACHMENT_V1"


def build_lr6_evid13_attachment_context() -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-EVID13",
        "metric_target": TARGET_METRIC,
        "scope": "dry_run_replay_observation_payload_attachment",
        "attachment_only": True,
        "dry_run_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "non_persistent": True,
    }


def identify_lr6_evid13_dry_run_attachment_targets() -> list[dict[str, Any]]:
    return [
        {
            "attachment_target": "lr6_obs7_simulated_wave_manifest",
            "source_module": "lr6_obs7_dry_run_enriched_replay_observation_simulation",
            "artifact_shape": "structured_replay_observation_manifest",
            "supports_structured_fields": True,
            "source_artifact_refs": [
                "module://lr6_obs7_dry_run_enriched_replay_observation_simulation",
                "artifact://simulated_wave_manifest",
            ],
            "notes": "Primary dry-run replay observation shape for structured replay richness counts.",
        }
    ]


def build_lr6_evid13_structured_artifact_adapter(source_artifact: dict[str, Any]) -> dict[str, Any]:
    artifact = source_artifact if isinstance(source_artifact, dict) else {}
    fields = {
        "replay_entity_count": artifact.get("replay_entity_count", artifact.get("candidate_count")),
        "distinct_candidate_count": artifact.get("distinct_candidate_count", artifact.get("candidate_count")),
        "distinct_role_count": artifact.get("distinct_role_count", artifact.get("role_count")),
        "distinct_cluster_count": artifact.get("distinct_cluster_count", artifact.get("cluster_count")),
    }
    refs = artifact.get("source_artifact_refs")
    if not isinstance(refs, list):
        refs = []

    return {
        **fields,
        "source_artifact_refs": refs,
        "measurement_basis": artifact.get("measurement_basis", "narrative_only"),
        "scaffold_only": bool(artifact.get("scaffold_only", False)),
        "before_after_comparison": deepcopy(artifact.get("before_after_comparison")) if isinstance(artifact.get("before_after_comparison"), dict) else None,
        "dry_run": True,
    }


def build_lr6_evid13_dry_run_emission_preview(attachment_target: str, source_artifact: dict[str, Any]) -> dict[str, Any]:
    adapted = build_lr6_evid13_structured_artifact_adapter(source_artifact)
    payload = build_lr6_evid11_replay_richness_payload(adapted)
    if payload["evidence_status"] == "MEASURED" and len(adapted["source_artifact_refs"]) == 0:
        payload = payload | {"evidence_status": "PARTIAL", "comparison_ready": False}

    emission_candidate = build_lr6_evid11_evid6_emission_candidate(adapted)
    status = payload["evidence_status"]

    return {
        "attachment_target": attachment_target,
        "source_artifact_refs": adapted["source_artifact_refs"],
        "extracted_structured_fields": adapted,
        "replay_richness_payload": payload,
        "evid6_compatible_emission_candidate": emission_candidate,
        "emission_status": "READY_DRY_RUN" if status == "MEASURED" else "REJECTED_OR_DOWNGRADED_DRY_RUN",
        "dry_run_only": True,
        "persisted": False,
        "live_ingestion": False,
        "governed_activation": False,
        "dry_run_caveat": "Preview-only attachment; no replay execution, persistence, ingestion, or governed activation.",
    }


def build_lr6_evid13_attachment_result(source_artifact: dict[str, Any]) -> dict[str, Any]:
    target = identify_lr6_evid13_dry_run_attachment_targets()[0]["attachment_target"]
    preview = build_lr6_evid13_dry_run_emission_preview(target, source_artifact)
    return {
        "context": build_lr6_evid13_attachment_context(),
        "attachment_target": target,
        "preview": preview,
        "boundary": certify_lr6_evid13_attachment_boundary(),
    }


def attach_lr6_evid13_replay_richness_payload_dry_run(source_artifact: dict[str, Any]) -> dict[str, Any]:
    return build_lr6_evid13_attachment_result(source_artifact)


def build_lr6_evid13_attachment_safety_review() -> dict[str, Any]:
    return {
        "dry_run_attachment_must_never_persist": True,
        "dry_run_attachment_must_never_call_live_ingestion": True,
        "dry_run_attachment_must_never_execute_replay": True,
        "dry_run_attachment_must_never_authorize_governed_activation": True,
        "comparison_ready_requires_explicit_baseline_fields": True,
        "scaffold_or_narrative_must_not_be_measured": True,
        "missing_lineage_must_not_remain_measured": True,
        "no_evid6_contract_change": True,
    }


def build_lr6_evid13_supervisor_review() -> dict[str, Any]:
    return {
        "objective": "Attach validated LR6-EVID11 replay_richness payload builder to dry-run replay observation artifact path only.",
        "inspected_evid11_evid12_builder_and_harness": [
            "lr6_evid11_first_real_replay_richness_payload_builder.py",
            "lr6_evid12_real_replay_richness_payload_validation_harness.py",
        ],
        "inspected_dry_run_replay_observation_paths": [
            "lr6_obs7_dry_run_enriched_replay_observation_simulation.py",
            "lr6_obs9_execution_review_framework.py",
            "lr6_exec2_first_dry_run_execution_review.py",
        ],
        "attachment_targets": identify_lr6_evid13_dry_run_attachment_targets(),
        "safety_review": build_lr6_evid13_attachment_safety_review(),
        "boundary_certification": certify_lr6_evid13_attachment_boundary(),
    }


def certify_lr6_evid13_attachment_boundary() -> dict[str, Any]:
    return {
        "dry_run_only": True,
        "attachment_only": True,
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


def build_lr6_evid13_markdown_report() -> str:
    review = build_lr6_evid13_supervisor_review()
    sample = build_lr6_evid13_attachment_result(
        {
            "candidate_count": 12,
            "role_count": 5,
            "cluster_count": 4,
            "measurement_basis": "structured_observation",
            "source_artifact_refs": ["artifact://obs7/sample"],
        }
    )
    lines = [
        "# LR6-EVID13 — Dry-Run Replay Richness Payload Attachment",
        "",
        "## objective",
        f"- {review['objective']}",
        "",
        "## inspected EVID11/EVID12 builder and harness",
    ]
    lines.extend([f"- {x}" for x in review["inspected_evid11_evid12_builder_and_harness"]])
    lines.extend(["", "## inspected dry-run replay observation paths"])
    lines.extend([f"- {x}" for x in review["inspected_dry_run_replay_observation_paths"]])
    lines.extend(["", "## attachment targets", f"- {review['attachment_targets']}"])
    lines.extend(["", "## structured artifact adapter", f"- {build_lr6_evid13_structured_artifact_adapter({})}"])
    lines.extend(["", "## dry-run emission preview", f"- {sample['preview']}"])
    lines.extend(["", "## scaffold/narrative rejection behavior", "- Scaffold-only and narrative-only artifacts are downgraded and never promoted to MEASURED."])
    lines.extend(["", "## EVID6 compatibility", "- EVID6-compatible emission candidate is generated via LR6-EVID11 candidate helper with no hook contract changes."])
    lines.extend(["", "## attachment safety review", f"- {build_lr6_evid13_attachment_safety_review()}"])
    lines.extend(["", "## boundary certification", f"- {certify_lr6_evid13_attachment_boundary()}"])
    lines.extend(["", "## recommendation for next step", "- Wire this dry-run preview into the actual replay observation rendering path while preserving dry-run-only and non-persistence controls."])
    return "\n".join(lines)

