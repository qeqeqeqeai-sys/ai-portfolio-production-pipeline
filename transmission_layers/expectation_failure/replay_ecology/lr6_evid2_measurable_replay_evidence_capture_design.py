"""LR6-EVID2 measurable replay evidence capture design (design-only, evidence-only)."""
from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_EVID2_MEASURABLE_REPLAY_EVIDENCE_CAPTURE_DESIGN_V1"
SOURCE_PHASE = "LR6-EVID2"

EVID1_DIMENSIONS = [
    "weak_signal_attribution",
    "contradiction_persistence_migration",
    "propagation_diversity",
    "topology_drift",
    "replay_saturation_monoculture",
    "megacap_semantic_gravity",
    "replay_richness",
]

EVIDENCE_STATUS_VALUES = {"MEASURED", "PARTIAL", "MISSING", "NOT_COMPARABLE", "SCAFFOLD_ONLY"}
REPLAY_PHASE_VALUES = {"BASELINE", "ENRICHED"}


def build_lr6_evid2_capture_design_context() -> dict[str, Any]:
    return {
        "meta": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "mode": "measurable_evidence_capture_design_only",
        },
        "basis": {
            "evid1a_run1_measurability_decision": "RUN1_SCAFFOLD_ONLY",
            "evid1_metric_population_status": "BLOCKED_SCAFFOLD_ONLY",
            "core_principle": "evidence_before_narrative",
        },
    }


def build_lr6_evid2_metric_field_definitions() -> list[dict[str, Any]]:
    return [
        {"metric_dimension": "weak_signal_attribution", "required_fields": ["weak_signal_attribution_count", "weak_signal_candidate_count", "weak_signal_attribution_ratio", "weak_signal_entities_observed", "weak_signal_entities_missing"]},
        {"metric_dimension": "contradiction_persistence_migration", "required_fields": ["contradiction_cluster_count", "persistent_contradiction_count", "migrated_contradiction_count", "cross_cluster_contradiction_count", "contradiction_persistence_ratio"]},
        {"metric_dimension": "propagation_diversity", "required_fields": ["propagation_bridge_count", "distinct_propagation_role_count", "non_obvious_bridge_count", "cross_cluster_bridge_count", "propagation_diversity_score"]},
        {"metric_dimension": "topology_drift", "required_fields": ["topology_drift_indicator", "new_bridge_count", "disappeared_bridge_count", "changed_bridge_count", "topology_drift_score"]},
        {"metric_dimension": "replay_saturation_monoculture", "required_fields": ["saturation_score", "concentration_score", "dominant_theme_share", "repeated_entity_share", "diversity_gain_indicator"]},
        {"metric_dimension": "megacap_semantic_gravity", "required_fields": ["megacap_attribution_count", "total_attribution_count", "megacap_concentration_ratio", "non_megacap_bridge_count", "megacap_gravity_status"]},
        {"metric_dimension": "replay_richness", "required_fields": ["replay_entity_count", "distinct_role_count", "distinct_cluster_count", "novel_bridge_count", "richness_score"]},
    ]


def build_lr6_evid2_evidence_record_schema() -> dict[str, Any]:
    return {
        "required_fields": [
            "evidence_record_id",
            "replay_phase",
            "wave_id",
            "candidate_scope_id",
            "candidate_count",
            "timestamp_or_snapshot_label",
            "metric_dimension",
            "measured_fields",
            "evidence_status",
            "source_artifact",
            "source_module",
            "comparison_ready",
            "scaffold_only",
            "notes",
        ],
        "replay_phase_values": sorted(REPLAY_PHASE_VALUES),
        "evidence_status_values": sorted(EVIDENCE_STATUS_VALUES),
        "notes": "Schema is for measurable capture design only; no execution, no persistence writes.",
    }


def _capture_requirements(phase: str) -> list[dict[str, Any]]:
    return [
        {
            "metric_dimension": row["metric_dimension"],
            "replay_phase": phase,
            "required_fields": row["required_fields"],
            "capture_rule": "Capture all required fields directly from replay evidence artifacts; no imputation.",
        }
        for row in build_lr6_evid2_metric_field_definitions()
    ]


def build_lr6_evid2_baseline_capture_requirements() -> list[dict[str, Any]]:
    return _capture_requirements("BASELINE")


def build_lr6_evid2_enriched_capture_requirements() -> list[dict[str, Any]]:
    return _capture_requirements("ENRICHED")


def build_lr6_evid2_pre_post_pairing_requirements() -> dict[str, Any]:
    return {
        "pairing_rules": [
            "same metric_dimension",
            "comparable candidate scope or documented scope difference",
            "same measurement definition",
            "same replay-window semantics",
            "same evidence status rules",
            "same no-imputation rule",
            "same no-scaffold-as-evidence rule",
        ]
    }


def build_lr6_evid2_quality_validation_rules() -> list[str]:
    return [
        "required fields must be present for MEASURED status",
        "scaffold_only=True cannot be comparison_ready=True",
        "missing baseline blocks improvement claim",
        "missing enriched evidence blocks improvement claim",
        "partial evidence cannot support structural improvement claim alone",
        "ratios must include numerator and denominator",
        "counts must be non-negative integers",
        "comparison_ready requires both baseline and enriched measurable records",
    ]


def build_lr6_evid2_no_scaffold_as_evidence_rules() -> dict[str, str]:
    return {
        "no_scaffold_as_evidence_rule": "Scaffold-only artifacts are never treated as measurable evidence.",
        "comparison_block_rule": "If scaffold_only=True on either side, set comparison_ready=False and block delta claims.",
        "status_rule": "Use evidence_status=SCAFFOLD_ONLY when evidence fields are placeholders or templates.",
    }


def build_lr6_evid2_evid1_population_mapping() -> list[dict[str, Any]]:
    rows = []
    for definition in build_lr6_evid2_metric_field_definitions():
        dim = definition["metric_dimension"]
        fields = definition["required_fields"]
        rows.append(
            {
                "metric_dimension": dim,
                "baseline_fields_required": list(fields),
                "enriched_fields_required": list(fields),
                "delta_formula_description": f"delta_{dim}=enriched_value-baseline_value at field level where numeric; for categorical fields compute explicit status transition.",
                "minimum_sufficiency_rule": "Both baseline and enriched records must be MEASURED, comparison_ready=True, scaffold_only=False.",
                "blockers_if_missing": "Missing/partial/scaffold-only on either side blocks structural improvement claim for this dimension.",
            }
        )
    return rows


def certify_lr6_evid2_capture_design_boundary() -> dict[str, Any]:
    return {
        "design_only": True,
        "evidence_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_evid2_supervisor_review() -> dict[str, Any]:
    return {
        "context": build_lr6_evid2_capture_design_context(),
        "evidence_record_schema": build_lr6_evid2_evidence_record_schema(),
        "baseline_capture_requirements": build_lr6_evid2_baseline_capture_requirements(),
        "enriched_capture_requirements": build_lr6_evid2_enriched_capture_requirements(),
        "metric_field_definitions": build_lr6_evid2_metric_field_definitions(),
        "pre_post_pairing_requirements": build_lr6_evid2_pre_post_pairing_requirements(),
        "quality_validation_rules": build_lr6_evid2_quality_validation_rules(),
        "no_scaffold_as_evidence_rules": build_lr6_evid2_no_scaffold_as_evidence_rules(),
        "evid1_population_mapping": build_lr6_evid2_evid1_population_mapping(),
        "boundary_certification": certify_lr6_evid2_capture_design_boundary(),
    }


def build_lr6_evid2_markdown_report() -> str:
    review = build_lr6_evid2_supervisor_review()
    return "\n".join([
        "# LR6-EVID2 Measurable Replay Evidence Capture Design",
        "## objective",
        "Define minimum measurable replay evidence fields so LR6-EVID1 pre/post delta tables can be populated with evidence.",
        "## EVID1/EVID1A basis",
        str(review["context"]["basis"]),
        "## evidence record schema",
        str(review["evidence_record_schema"]),
        "## baseline capture requirements",
        str(review["baseline_capture_requirements"]),
        "## enriched capture requirements",
        str(review["enriched_capture_requirements"]),
        "## metric field definitions",
        str(review["metric_field_definitions"]),
        "## pre/post pairing requirements",
        str(review["pre_post_pairing_requirements"]),
        "## quality validation rules",
        str(review["quality_validation_rules"]),
        "## no-scaffold-as-evidence rules",
        str(review["no_scaffold_as_evidence_rules"]),
        "## EVID1 population mapping",
        str(review["evid1_population_mapping"]),
        "## boundary certification",
        str(review["boundary_certification"]),
        "## recommendation for next step",
        "Implement capture emitters that populate this schema in baseline and enriched replay, then re-run EVID1 with strict no-scaffold enforcement.",
    ])


__all__ = [n for n in globals() if n.startswith("build_lr6_evid2_") or n == "certify_lr6_evid2_capture_design_boundary" or n in {"EVID1_DIMENSIONS", "EVIDENCE_STATUS_VALUES", "REPLAY_PHASE_VALUES"}]
