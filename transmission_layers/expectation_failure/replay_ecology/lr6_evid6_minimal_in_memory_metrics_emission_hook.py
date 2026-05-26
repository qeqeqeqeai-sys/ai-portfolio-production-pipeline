"""LR6-EVID6 minimal in-memory metrics emission hook (hook-only, evidence-only)."""
from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_evid1a_evidence_source_mapping import EVID1_DIMENSIONS

DETERMINISTIC_VERSION = "LR6_EVID6_MINIMAL_IN_MEMORY_METRICS_EMISSION_HOOK_V1"
SOURCE_PHASE = "LR6-EVID6"
VALID_REPLAY_PHASES = {"BASELINE", "ENRICHED"}
EVIDENCE_STATUS_VALUES = {"MEASURED", "PARTIAL", "MISSING", "NOT_COMPARABLE", "SCAFFOLD_ONLY"}
SCAFFOLD_MARKERS = {
    "governance_review",
    "supervisor_review",
    "expected_artifacts",
    "review_sections",
    "final_decision",
    "approval_gate",
    "dry_run",
    "execution_authorized",
}


def build_lr6_evid6_hook_context() -> dict[str, Any]:
    return {
        "meta": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "mode": "minimal_in_memory_metrics_emission_hook",
        },
        "basis": {
            "evid5_design": "minimal replay-time measurable metrics emission hook",
            "target": "emit EVID2/EVID3-compatible evidence records from explicit metric payload fields only",
        },
    }


def build_lr6_evid6_supported_metric_dimensions() -> list[str]:
    return list(EVID1_DIMENSIONS)


def build_lr6_evid6_required_field_contract() -> dict[str, list[str]]:
    return {
        "weak_signal_attribution": ["weak_signal_attribution_count", "weak_signal_candidate_count", "weak_signal_attribution_ratio", "weak_signal_entities_observed", "weak_signal_entities_missing"],
        "contradiction_persistence_migration": ["contradiction_cluster_count", "persistent_contradiction_count", "migrated_contradiction_count", "cross_cluster_contradiction_count", "contradiction_persistence_ratio"],
        "propagation_diversity": ["propagation_bridge_count", "distinct_propagation_role_count", "non_obvious_bridge_count", "cross_cluster_bridge_count", "propagation_diversity_score"],
        "topology_drift": ["topology_drift_indicator", "new_bridge_count", "disappeared_bridge_count", "changed_bridge_count", "topology_drift_score"],
        "replay_saturation_monoculture": ["saturation_score", "concentration_score", "dominant_theme_share", "repeated_entity_share", "diversity_gain_indicator"],
        "megacap_semantic_gravity": ["megacap_attribution_count", "total_attribution_count", "megacap_concentration_ratio", "non_megacap_bridge_count", "megacap_gravity_status"],
        "replay_richness": ["replay_entity_count", "distinct_role_count", "distinct_cluster_count", "novel_bridge_count", "richness_score"],
    }


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_zero_to_one_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_field(field_name: str, value: Any) -> bool:
    if field_name.endswith("_count"):
        return _is_non_negative_int(value)
    if field_name.endswith("_ratio") or field_name.endswith("_share") or field_name.endswith("_score"):
        return _is_zero_to_one_numeric(value)
    if field_name in {"weak_signal_entities_observed", "weak_signal_entities_missing"}:
        return isinstance(value, list)
    if field_name in {"topology_drift_indicator", "diversity_gain_indicator"}:
        return isinstance(value, bool)
    if field_name == "megacap_gravity_status":
        return _is_non_empty_string(value)
    return value is not None


def _extract_metric_bucket(payload: dict[str, Any], metric_dimension: str) -> dict[str, Any]:
    options: list[Any] = []
    metrics = payload.get("metrics")
    if isinstance(metrics, dict):
        options.append(metrics.get(metric_dimension))
    options.append(payload.get(metric_dimension))
    measured_fields = payload.get("measured_fields")
    if isinstance(measured_fields, dict):
        options.append(measured_fields.get(metric_dimension))
    for candidate in options:
        if isinstance(candidate, dict):
            return candidate
    return {}


def validate_lr6_evid6_metric_payload(*, metric_dimension: str, metric_payload: dict[str, Any]) -> dict[str, Any]:
    required = build_lr6_evid6_required_field_contract()[metric_dimension]
    measured = {k: metric_payload[k] for k in required if k in metric_payload and _validate_field(k, metric_payload[k])}
    invalid_fields = sorted([k for k in required if k in metric_payload and not _validate_field(k, metric_payload[k])])
    return {
        "metric_dimension": metric_dimension,
        "required_fields": required,
        "measured_fields": measured,
        "invalid_fields": invalid_fields,
        "measured_field_count": len(measured),
    }


def _is_scaffold_only_payload(payload: dict[str, Any]) -> bool:
    return any(marker in payload for marker in SCAFFOLD_MARKERS)


def emit_lr6_replay_metric_evidence(*, replay_phase: str, wave_id: str, candidate_scope_id: str, candidate_count: int, timestamp_or_snapshot_label: str, replay_observation_payload: dict, candidate_metadata: dict | list | None = None, baseline_reference_payload: dict | None = None, source_artifact: str = "in_memory_replay_observation_payload", source_module: str = "lr6_evid6_minimal_in_memory_metrics_emission_hook") -> list[dict]:
    contract = build_lr6_evid6_required_field_contract()
    payload = replay_observation_payload if isinstance(replay_observation_payload, dict) else {}

    not_comparable = not (
        replay_phase in VALID_REPLAY_PHASES
        and _is_non_empty_string(wave_id)
        and _is_non_empty_string(candidate_scope_id)
        and _is_non_empty_string(timestamp_or_snapshot_label)
        and _is_non_negative_int(candidate_count)
    )

    records = []
    scaffold_payload = _is_scaffold_only_payload(payload)
    for metric_dimension in EVID1_DIMENSIONS:
        validation = validate_lr6_evid6_metric_payload(metric_dimension=metric_dimension, metric_payload=_extract_metric_bucket(payload, metric_dimension))
        measured_fields = validation["measured_fields"]
        required_count = len(contract[metric_dimension])
        measured_count = validation["measured_field_count"]

        if not_comparable:
            status = "NOT_COMPARABLE"
        elif measured_count == required_count:
            status = "MEASURED"
        elif measured_count > 0:
            status = "PARTIAL"
        elif scaffold_payload:
            status = "SCAFFOLD_ONLY"
        else:
            status = "MISSING"

        scaffold_only = status == "SCAFFOLD_ONLY"
        comparison_ready = bool(
            status == "MEASURED"
            and not scaffold_only
            and replay_phase in VALID_REPLAY_PHASES
            and _is_non_empty_string(wave_id)
            and _is_non_empty_string(candidate_scope_id)
            and _is_non_empty_string(timestamp_or_snapshot_label)
        )
        notes = f"coverage={measured_count}/{required_count}; invalid_fields={validation['invalid_fields']}"
        records.append(
            {
                "evidence_record_id": f"{replay_phase}:{metric_dimension}:{candidate_scope_id or 'UNSCOPED'}:{wave_id or timestamp_or_snapshot_label or 'UNSTAMPED'}",
                "replay_phase": replay_phase,
                "wave_id": wave_id,
                "candidate_scope_id": candidate_scope_id,
                "candidate_count": candidate_count,
                "timestamp_or_snapshot_label": timestamp_or_snapshot_label,
                "metric_dimension": metric_dimension,
                "measured_fields": measured_fields,
                "evidence_status": status,
                "source_artifact": source_artifact,
                "source_module": source_module,
                "comparison_ready": comparison_ready,
                "scaffold_only": scaffold_only,
                "notes": notes,
            }
        )
    return records


def build_lr6_evid6_emission_quality_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = {s: 0 for s in sorted(EVIDENCE_STATUS_VALUES)}
    for record in records:
        status_counts[record["evidence_status"]] = status_counts.get(record["evidence_status"], 0) + 1
    return {"total_records": len(records), "status_counts": status_counts}


def build_lr6_evid6_evid3_compatibility_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    required_keys = ["evidence_record_id", "replay_phase", "wave_id", "candidate_scope_id", "candidate_count", "timestamp_or_snapshot_label", "metric_dimension", "measured_fields", "evidence_status", "source_artifact", "source_module", "comparison_ready", "scaffold_only", "notes"]
    key_ok = all(all(k in r for k in required_keys) for r in records)
    return {
        "record_count": len(records),
        "expected_record_count": 7,
        "all_required_keys_present": key_ok,
        "supported_status_values": sorted(EVIDENCE_STATUS_VALUES),
    }


def certify_lr6_evid6_hook_boundary() -> dict[str, Any]:
    return {
        "hook_only": True,
        "in_memory_only": True,
        "evidence_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "no_interpretation_claims": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_evid6_supervisor_review() -> dict[str, Any]:
    return {
        "context": build_lr6_evid6_hook_context(),
        "supported_metric_dimensions": build_lr6_evid6_supported_metric_dimensions(),
        "required_field_contract": build_lr6_evid6_required_field_contract(),
        "extraction_rules": [
            'payload["metrics"][metric_dimension]',
            'payload[metric_dimension]',
            'payload["measured_fields"][metric_dimension]',
        ],
        "status_rules": ["MEASURED", "PARTIAL", "MISSING", "NOT_COMPARABLE", "SCAFFOLD_ONLY"],
        "validation_rules": [
            "counts must be non-negative integers",
            "ratio/share/score fields must be in [0,1]",
            "replay_phase must be BASELINE or ENRICHED",
            "candidate_count must be non-negative integer",
            "required identifiers must be non-empty strings",
        ],
        "scaffold_detection_markers": sorted(SCAFFOLD_MARKERS),
        "boundary_certification": certify_lr6_evid6_hook_boundary(),
        "recommendation": "Invoke this hook from replay execution output only after observed metric fields are explicitly populated.",
    }


def build_lr6_evid6_markdown_report() -> str:
    review = build_lr6_evid6_supervisor_review()
    return "\n".join([
        "# LR6-EVID6 Minimal In-Memory Metrics Emission Hook",
        "## objective",
        "Implement a deterministic in-memory emission hook that returns evidence records from explicit metric fields only.",
        "## EVID5 basis",
        str(review["context"]["basis"]),
        "## hook signature",
        "emit_lr6_replay_metric_evidence(*, replay_phase, wave_id, candidate_scope_id, candidate_count, timestamp_or_snapshot_label, replay_observation_payload, candidate_metadata=None, baseline_reference_payload=None, source_artifact='in_memory_replay_observation_payload', source_module='lr6_evid6_minimal_in_memory_metrics_emission_hook') -> list[dict]",
        "## supported metric dimensions",
        str(review["supported_metric_dimensions"]),
        "## required field contract",
        str(review["required_field_contract"]),
        "## extraction rules",
        str(review["extraction_rules"]),
        "## status rules",
        "MEASURED when all required fields are valid; PARTIAL when some are valid; MISSING when none are valid; SCAFFOLD_ONLY when scaffold markers exist with no measurable fields; NOT_COMPARABLE when identifiers/phase/count fail comparability constraints.",
        "## validation rules",
        str(review["validation_rules"]),
        "## scaffold detection",
        str(review["scaffold_detection_markers"]),
        "## EVID3 compatibility",
        "Records carry EVID2/EVID3-compatible fields and statuses with deterministic key coverage.",
        "## boundary certification",
        str(review["boundary_certification"]),
        "## recommendation for next step",
        review["recommendation"],
    ])


__all__ = [
    "emit_lr6_replay_metric_evidence",
    "build_lr6_evid6_hook_context",
    "build_lr6_evid6_supported_metric_dimensions",
    "build_lr6_evid6_required_field_contract",
    "validate_lr6_evid6_metric_payload",
    "build_lr6_evid6_emission_quality_summary",
    "build_lr6_evid6_evid3_compatibility_summary",
    "build_lr6_evid6_supervisor_review",
    "build_lr6_evid6_markdown_report",
    "certify_lr6_evid6_hook_boundary",
]
