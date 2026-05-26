"""LR6-EVID1A baseline/enriched evidence source mapping (mapping-only, evidence-only)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

DETERMINISTIC_VERSION = "LR6_EVID1A_EVIDENCE_SOURCE_MAPPING_V1"
SOURCE_PHASE = "LR6-EVID1A"

SOURCE_STATUS_VALUES = {"AVAILABLE", "PARTIAL", "MISSING", "SCAFFOLD_ONLY", "NOT_MEASURABLE"}
METRIC_POPULATION_STATUS_VALUES = {
    "READY",
    "PARTIAL",
    "BLOCKED_MISSING_BASELINE",
    "BLOCKED_MISSING_ENRICHED",
    "BLOCKED_MISSING_BOTH",
    "BLOCKED_SCAFFOLD_ONLY",
}
RUN1_MEASURABILITY_VALUES = {
    "RUN1_MEASURABLE_EVIDENCE_AVAILABLE",
    "RUN1_PARTIAL_EVIDENCE_AVAILABLE",
    "RUN1_SCAFFOLD_ONLY",
    "RUN1_EVIDENCE_MISSING",
}
EVID1_DIMENSIONS = [
    "weak_signal_attribution",
    "contradiction_persistence_migration",
    "propagation_diversity",
    "topology_drift",
    "replay_saturation_monoculture",
    "megacap_semantic_gravity",
    "replay_richness",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _exists(path: str) -> bool:
    return (_repo_root() / path).exists()


def _build_source(*, source_name: str, source_path: str, source_type: str, baseline_or_enriched: str, evidence_dimensions_supported: list[str], measurable_fields_available: list[str], status: str) -> dict[str, Any]:
    return {
        "source_name": source_name,
        "source_path": source_path,
        "source_type": source_type,
        "baseline_or_enriched": baseline_or_enriched,
        "evidence_dimensions_supported": list(evidence_dimensions_supported),
        "measurable_fields_available": list(measurable_fields_available),
        "status": status,
    }


def build_lr6_evid1a_source_mapping_context() -> dict[str, Any]:
    inspected = [
        "reports/lr6_evid1_pre_post_replay_delta_evidence.md",
        "reports/lr6_run2_post_wave_evidence_audit.md",
        "reports/lr6_exec2_first_dry_run_execution_review.md",
        "reports/lr6_obs9_execution_review_framework.md",
        "reports/lr6_exp6_replay_ecology_snapshot_export.md",
        "reports/lr6_exp6a_longitudinal_snapshot_comparison.md",
        "reports/lr6_exp7_replay_ecology_interestingness_scoring.md",
        "reports/lr6_exp8_replay_ecology_findings_report.md",
        "transmission_layers/expectation_failure/replay_ecology/lr6_evid1_pre_post_replay_delta_evidence.py",
        "transmission_layers/expectation_failure/replay_ecology/lr6_run1_single_governed_observation_wave.py",
        "transmission_layers/expectation_failure/replay_ecology/lr6_exec2_first_dry_run_execution_review.py",
        "transmission_layers/expectation_failure/replay_ecology/lr6_obs6_first_enriched_replay_wave_design.py",
    ]
    return {
        "meta": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "mode": "evidence_source_mapping_only",
        },
        "inspected_artifacts": [{"path": p, "exists": _exists(p)} for p in inspected],
    }


def build_lr6_evid1a_baseline_source_inventory(context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [
        _build_source(source_name="LR6-EXP6 Snapshot Export", source_path="reports/lr6_exp6_replay_ecology_snapshot_export.md", source_type="pre_enrichment_snapshot_report", baseline_or_enriched="baseline", evidence_dimensions_supported=EVID1_DIMENSIONS, measurable_fields_available=[], status="SCAFFOLD_ONLY"),
        _build_source(source_name="LR6-EXP6A Longitudinal Snapshot Comparison", source_path="reports/lr6_exp6a_longitudinal_snapshot_comparison.md", source_type="longitudinal_comparison_report", baseline_or_enriched="baseline", evidence_dimensions_supported=["topology_drift", "replay_richness"], measurable_fields_available=[], status="SCAFFOLD_ONLY"),
        _build_source(source_name="LR6-EXP7 Interestingness Scoring", source_path="reports/lr6_exp7_replay_ecology_interestingness_scoring.md", source_type="interestingness_report", baseline_or_enriched="baseline", evidence_dimensions_supported=["weak_signal_attribution", "propagation_diversity"], measurable_fields_available=[], status="NOT_MEASURABLE"),
        _build_source(source_name="LR6-EXP8 Findings Report", source_path="reports/lr6_exp8_replay_ecology_findings_report.md", source_type="findings_report", baseline_or_enriched="baseline", evidence_dimensions_supported=EVID1_DIMENSIONS, measurable_fields_available=[], status="SCAFFOLD_ONLY"),
        _build_source(source_name="Pre-RUN1 Replay Metadata", source_path="reports/ix_longitudinal_replay_review.json", source_type="metadata_export", baseline_or_enriched="baseline", evidence_dimensions_supported=["replay_richness", "topology_drift"], measurable_fields_available=["snapshot_count"], status="PARTIAL"),
    ]


def build_lr6_evid1a_enriched_source_inventory(context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [
        _build_source(source_name="LR6-RUN1 Execution Output", source_path="transmission_layers/expectation_failure/replay_ecology/lr6_run1_single_governed_observation_wave.py", source_type="run_execution_module", baseline_or_enriched="enriched", evidence_dimensions_supported=EVID1_DIMENSIONS, measurable_fields_available=[], status="SCAFFOLD_ONLY"),
        _build_source(source_name="RUN1 Review Artifacts", source_path="reports/lr6_exec2_first_dry_run_execution_review.md", source_type="run_review_report", baseline_or_enriched="enriched", evidence_dimensions_supported=EVID1_DIMENSIONS, measurable_fields_available=[], status="SCAFFOLD_ONLY"),
        _build_source(source_name="RUN2 Post-Wave Evidence Audit", source_path="reports/lr6_run2_post_wave_evidence_audit.md", source_type="post_wave_audit_report", baseline_or_enriched="enriched", evidence_dimensions_supported=EVID1_DIMENSIONS, measurable_fields_available=[], status="SCAFFOLD_ONLY"),
        _build_source(source_name="Weak-Signal Attribution Outputs", source_path="reports/lr6_evid1_pre_post_replay_delta_evidence.md", source_type="delta_evidence_report", baseline_or_enriched="enriched", evidence_dimensions_supported=["weak_signal_attribution"], measurable_fields_available=[], status="MISSING"),
        _build_source(source_name="Topology Delta Outputs", source_path="reports/lr6_obs9_execution_review_framework.md", source_type="execution_review_framework", baseline_or_enriched="enriched", evidence_dimensions_supported=["topology_drift", "replay_saturation_monoculture"], measurable_fields_available=[], status="SCAFFOLD_ONLY"),
    ]


def build_lr6_evid1a_metric_source_map(context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = []
    for dim in EVID1_DIMENSIONS:
        rows.append(
            {
                "metric": dim,
                "baseline_source_candidate": "LR6-EXP6 Snapshot Export",
                "enriched_source_candidate": "LR6-RUN1 Execution Output",
                "required_baseline_fields": [f"baseline_{dim}_value"],
                "required_enriched_fields": [f"enriched_{dim}_value"],
                "current_availability": "No paired measurable baseline/enriched values found.",
                "blocker_if_missing": "Missing measurable baseline and/or enriched paired fields.",
                "population_status": "BLOCKED_SCAFFOLD_ONLY",
            }
        )
    return rows


def build_lr6_evid1a_missing_metric_inventory(metric_source_map: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    source = metric_source_map or build_lr6_evid1a_metric_source_map()
    return [
        {
            "metric": row["metric"],
            "missing_baseline_fields": row["required_baseline_fields"],
            "missing_enriched_fields": row["required_enriched_fields"],
            "blocker": row["population_status"],
        }
        for row in source
        if row["population_status"] != "READY"
    ]


def build_lr6_evid1a_minimum_evidence_requirements() -> list[dict[str, Any]]:
    return [
        {"metric": "weak_signal_attribution", "required_fields": ["baseline_weak_signal_attribution_count", "enriched_weak_signal_attribution_count"]},
        {"metric": "contradiction_persistence_migration", "required_fields": ["baseline_contradiction_persistence_count", "enriched_contradiction_persistence_count"]},
        {"metric": "propagation_diversity", "required_fields": ["baseline_propagation_bridge_diversity_count", "enriched_propagation_bridge_diversity_count"]},
        {"metric": "topology_drift", "required_fields": ["baseline_topology_drift_indicator", "enriched_topology_drift_indicator"]},
        {"metric": "replay_saturation_monoculture", "required_fields": ["baseline_saturation_concentration_score", "enriched_saturation_concentration_score"]},
        {"metric": "megacap_semantic_gravity", "required_fields": ["baseline_megacap_concentration_ratio", "enriched_megacap_concentration_ratio"]},
        {"metric": "replay_richness", "required_fields": ["baseline_replay_richness_indicator", "enriched_replay_richness_indicator"]},
    ]


def build_lr6_evid1a_run1_output_measurability_review(context: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "decision": "RUN1_SCAFFOLD_ONLY",
        "basis": "Available RUN1/RUN2 artifacts indicate deterministic review scaffolding without paired measurable enriched replay evidence fields.",
    }


def build_lr6_evid1a_evid1_population_plan(metric_source_map: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    source = metric_source_map or build_lr6_evid1a_metric_source_map()
    return {
        "dimension_population_plan": [
            {
                "metric": row["metric"],
                "feed_sources": [row["baseline_source_candidate"], row["enriched_source_candidate"]],
                "mandatory_fields": row["required_baseline_fields"] + row["required_enriched_fields"],
                "blocked_if_missing": row["population_status"] != "READY",
            }
            for row in source
        ],
        "rules": {
            "no_imputation_rule": "Do not synthesize missing baseline or enriched values.",
            "no_scaffold_as_evidence_rule": "Do not treat review scaffolding artifacts as measured evidence.",
            "evidence_before_narrative_rule": "Do not produce improvement narrative before paired measurable evidence exists.",
        },
    }


def certify_lr6_evid1a_mapping_boundary() -> dict[str, Any]:
    return {
        "mapping_only": True,
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


def build_lr6_evid1a_supervisor_review(context: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = context or build_lr6_evid1a_source_mapping_context()
    baseline = build_lr6_evid1a_baseline_source_inventory(ctx)
    enriched = build_lr6_evid1a_enriched_source_inventory(ctx)
    metric_map = build_lr6_evid1a_metric_source_map(ctx)
    return {
        "context_meta": ctx["meta"],
        "baseline_source_inventory": baseline,
        "enriched_source_inventory": enriched,
        "metric_source_map": metric_map,
        "missing_metric_inventory": build_lr6_evid1a_missing_metric_inventory(metric_map),
        "run1_measurability_review": build_lr6_evid1a_run1_output_measurability_review(ctx),
        "minimum_evidence_requirements": build_lr6_evid1a_minimum_evidence_requirements(),
        "evid1_population_plan": build_lr6_evid1a_evid1_population_plan(metric_map),
        "mapping_boundary": certify_lr6_evid1a_mapping_boundary(),
    }


def build_lr6_evid1a_markdown_report(context: dict[str, Any] | None = None) -> str:
    review = build_lr6_evid1a_supervisor_review(context)
    return "\n".join([
        "# LR6-EVID1A Evidence Source Mapping",
        "## objective",
        "Map concrete measurable baseline/enriched evidence sources required to populate LR6-EVID1 delta tables.",
        "## inspected artifacts/modules",
        str(review["context_meta"]),
        "## baseline source inventory",
        str(review["baseline_source_inventory"]),
        "## enriched source inventory",
        str(review["enriched_source_inventory"]),
        "## metric source map",
        str(review["metric_source_map"]),
        "## missing metric inventory",
        str(review["missing_metric_inventory"]),
        "## RUN1 measurability review",
        str(review["run1_measurability_review"]),
        "## minimum evidence requirements",
        str(review["minimum_evidence_requirements"]),
        "## EVID1 population plan",
        str(review["evid1_population_plan"]),
        "## mapping boundary",
        str(review["mapping_boundary"]),
        "## recommendation",
        "Keep all EVID1 ecological-improvement claims blocked until paired measurable baseline and enriched fields exist for every mapped metric.",
    ])


__all__ = [n for n in globals() if n.startswith("build_lr6_evid1a_") or n == "certify_lr6_evid1a_mapping_boundary" or n in {"SOURCE_STATUS_VALUES", "METRIC_POPULATION_STATUS_VALUES", "RUN1_MEASURABILITY_VALUES", "EVID1_DIMENSIONS"}]
