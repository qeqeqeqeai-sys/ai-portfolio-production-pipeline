"""LR6-EVID3 measurable evidence capture adapter (adapter-only, evidence-only)."""
from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_evid2_measurable_replay_evidence_capture_design import (
    EVID1_DIMENSIONS,
    build_lr6_evid2_metric_field_definitions,
)

DETERMINISTIC_VERSION = "LR6_EVID3_MEASURABLE_EVIDENCE_CAPTURE_ADAPTER_V1"
SOURCE_PHASE = "LR6-EVID3"
EVIDENCE_STATUS_VALUES = {"MEASURED", "PARTIAL", "MISSING", "NOT_COMPARABLE", "SCAFFOLD_ONLY"}
REPLAY_PHASE_VALUES = {"BASELINE", "ENRICHED", "RUN1_REVIEW", "EXP6_SNAPSHOT", "EXP7_INTERESTINGNESS", "EXP8_FINDINGS"}


def build_lr6_evid3_adapter_context() -> dict[str, Any]:
    return {
        "meta": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "mode": "measurable_evidence_capture_adapter_only",
        },
        "basis": {
            "evid1_decision": "BASELINE_OR_ENRICHED_EVIDENCE_MISSING",
            "evid1a_decision": "RUN1_SCAFFOLD_ONLY",
            "evid2_contract": "minimum measurable evidence schema",
        },
    }


def build_lr6_evid3_supported_payload_contracts() -> list[dict[str, str]]:
    return [
        {"payload_kind": "baseline_replay_payload", "default_replay_phase": "BASELINE"},
        {"payload_kind": "enriched_replay_payload", "default_replay_phase": "ENRICHED"},
        {"payload_kind": "run1_review_artifact_payload", "default_replay_phase": "RUN1_REVIEW"},
        {"payload_kind": "exp6_exp6a_snapshot_payload", "default_replay_phase": "EXP6_SNAPSHOT"},
        {"payload_kind": "exp7_interestingness_payload", "default_replay_phase": "EXP7_INTERESTINGNESS"},
        {"payload_kind": "exp8_findings_payload", "default_replay_phase": "EXP8_FINDINGS"},
    ]


def build_lr6_evid3_metric_extractors() -> dict[str, Any]:
    req = {row["metric_dimension"]: list(row["required_fields"]) for row in build_lr6_evid2_metric_field_definitions()}
    return {dim: {"required_fields": req[dim], "rule": "no narrative-only inference"} for dim in EVID1_DIMENSIONS}


def _is_scaffold_only_payload(payload: dict[str, Any]) -> bool:
    metrics = payload.get("metrics") if isinstance(payload, dict) else None
    has_metric_values = isinstance(metrics, dict) and any(isinstance(v, dict) and v for v in metrics.values())
    scaffold_cues = any(k in payload for k in ["review", "governance", "expected_artifacts", "claims", "narrative"])
    candidate_lists_only = "candidates" in payload and not has_metric_values
    return bool((scaffold_cues or candidate_lists_only) and not has_metric_values)


def _extract_metric(payload: dict[str, Any], metric_dimension: str, required_fields: list[str]) -> tuple[dict[str, Any], str]:
    metric_bucket = payload.get("metrics", {}).get(metric_dimension, {}) if isinstance(payload.get("metrics"), dict) else {}
    measured = {k: metric_bucket[k] for k in required_fields if k in metric_bucket and metric_bucket[k] is not None}
    if _is_scaffold_only_payload(payload):
        return {}, "SCAFFOLD_ONLY"
    if len(measured) == len(required_fields):
        return measured, "MEASURED"
    if measured:
        return measured, "PARTIAL"
    return {}, "MISSING"


def adapt_lr6_evid3_payload_to_evidence_records(payload: dict[str, Any], replay_phase: str, source_artifact: str, source_module: str) -> list[dict[str, Any]]:
    extractors = build_lr6_evid3_metric_extractors()
    wave_id = payload.get("wave_id")
    scope_id = payload.get("candidate_scope_id")
    snapshot = payload.get("timestamp_or_snapshot_label")
    candidate_count = payload.get("candidate_count")
    records = []
    for metric_dimension in EVID1_DIMENSIONS:
        required_fields = extractors[metric_dimension]["required_fields"]
        measured_fields, status = _extract_metric(payload, metric_dimension, required_fields)
        scaffold_only = status == "SCAFFOLD_ONLY"
        comparison_ready = bool(
            status == "MEASURED"
            and not scaffold_only
            and replay_phase in {"BASELINE", "ENRICHED"}
            and scope_id
            and (wave_id or snapshot)
        )
        notes = "measured field coverage: " + str(len(measured_fields)) + "/" + str(len(required_fields))
        records.append(
            {
                "evidence_record_id": f"{replay_phase}:{metric_dimension}:{scope_id or 'UNSCOPED'}:{wave_id or snapshot or 'UNWAVED'}",
                "replay_phase": replay_phase,
                "wave_id": wave_id,
                "candidate_scope_id": scope_id,
                "candidate_count": candidate_count,
                "timestamp_or_snapshot_label": snapshot,
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


def adapt_lr6_evid3_baseline_payload(payload: dict[str, Any], source_artifact: str = "baseline_payload", source_module: str = "replay_ecology") -> list[dict[str, Any]]:
    return adapt_lr6_evid3_payload_to_evidence_records(payload, "BASELINE", source_artifact, source_module)


def adapt_lr6_evid3_enriched_payload(payload: dict[str, Any], source_artifact: str = "enriched_payload", source_module: str = "replay_ecology") -> list[dict[str, Any]]:
    return adapt_lr6_evid3_payload_to_evidence_records(payload, "ENRICHED", source_artifact, source_module)


def build_lr6_evid3_extraction_quality_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = {s: 0 for s in sorted(EVIDENCE_STATUS_VALUES)}
    for r in records:
        by_status[r["evidence_status"]] = by_status.get(r["evidence_status"], 0) + 1
    return {"total_records": len(records), "status_counts": by_status}


def build_lr6_evid3_comparison_readiness_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [r for r in records if r["comparison_ready"]]
    blocked = [r for r in records if not r["comparison_ready"]]
    return {"comparison_ready_count": len(ready), "blocked_count": len(blocked), "ready_dimensions": sorted({r["metric_dimension"] for r in ready})}


def build_lr6_evid3_evid1_ready_payload(baseline_records: list[dict[str, Any]], enriched_records: list[dict[str, Any]]) -> dict[str, Any]:
    b_by = {r["metric_dimension"]: r for r in baseline_records}
    e_by = {r["metric_dimension"]: r for r in enriched_records}
    paired = sorted([d for d in EVID1_DIMENSIONS if d in b_by and d in e_by])
    blocked = sorted([d for d in paired if not (b_by[d]["comparison_ready"] and e_by[d]["comparison_ready"])])
    missing_b = sorted([d for d in EVID1_DIMENSIONS if d not in b_by or b_by[d]["evidence_status"] in {"MISSING", "SCAFFOLD_ONLY"}])
    missing_e = sorted([d for d in EVID1_DIMENSIONS if d not in e_by or e_by[d]["evidence_status"] in {"MISSING", "SCAFFOLD_ONLY"}])
    scaffold_dims = sorted([d for d in paired if b_by[d]["scaffold_only"] or e_by[d]["scaffold_only"]])
    ready_dims = sorted([d for d in paired if b_by[d]["comparison_ready"] and e_by[d]["comparison_ready"]])
    return {
        "baseline_records": baseline_records,
        "enriched_records": enriched_records,
        "paired_dimensions": paired,
        "blocked_dimensions": blocked,
        "missing_baseline_dimensions": missing_b,
        "missing_enriched_dimensions": missing_e,
        "scaffold_only_dimensions": scaffold_dims,
        "comparison_ready_dimensions": ready_dims,
    }


def certify_lr6_evid3_adapter_boundary() -> dict[str, Any]:
    return {
        "adapter_only": True,
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


def build_lr6_evid3_supervisor_review() -> dict[str, Any]:
    return {
        "context": build_lr6_evid3_adapter_context(),
        "supported_payload_contracts": build_lr6_evid3_supported_payload_contracts(),
        "metric_extractors": build_lr6_evid3_metric_extractors(),
        "boundary_certification": certify_lr6_evid3_adapter_boundary(),
    }


def build_lr6_evid3_markdown_report() -> str:
    review = build_lr6_evid3_supervisor_review()
    return "\n".join([
        "# LR6-EVID3 Measurable Evidence Capture Adapter",
        "## objective",
        "Implement a deterministic adapter that converts replay artifacts into EVID2-style evidence records.",
        "## EVID1/EVID1A/EVID2 basis",
        str(review["context"]["basis"]),
        "## supported payload contracts",
        str(review["supported_payload_contracts"]),
        "## evidence record output structure",
        "evidence_record_id, replay_phase, wave_id, candidate_scope_id, candidate_count, timestamp_or_snapshot_label, metric_dimension, measured_fields, evidence_status, source_artifact, source_module, comparison_ready, scaffold_only, notes",
        "## metric extractors",
        str(review["metric_extractors"]),
        "## scaffold-only detection",
        "Review/governance/textual-only payloads without measured metric fields are marked SCAFFOLD_ONLY.",
        "## comparison readiness rules",
        "MEASURED + non-scaffold + BASELINE/ENRICHED + candidate_scope_id + (wave_id or snapshot).",
        "## EVID1-ready payload format",
        "baseline_records, enriched_records, paired_dimensions, blocked_dimensions, missing_baseline_dimensions, missing_enriched_dimensions, scaffold_only_dimensions, comparison_ready_dimensions",
        "## quality report behavior",
        "Status-count summaries and comparison-readiness summaries are deterministic and record-driven.",
        "## boundary certification",
        str(review["boundary_certification"]),
        "## recommendation for next step",
        "Run EVID1 delta population using only comparison-ready records and keep scaffold-only artifacts blocked.",
    ])


__all__ = [n for n in globals() if n.startswith("build_lr6_evid3_") or n.startswith("adapt_lr6_evid3_") or n == "certify_lr6_evid3_adapter_boundary"]
