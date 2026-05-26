"""LR6-EVID4 first real evidence record emission review (emission-review-only)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_evid2_measurable_replay_evidence_capture_design import EVID1_DIMENSIONS
from transmission_layers.expectation_failure.replay_ecology.lr6_evid3_measurable_evidence_capture_adapter import (
    EVIDENCE_STATUS_VALUES,
    adapt_lr6_evid3_payload_to_evidence_records,
)

DETERMINISTIC_VERSION = "LR6_EVID4_FIRST_REAL_EVIDENCE_RECORD_EMISSION_REVIEW_V1"
SOURCE_PHASE = "LR6-EVID4"
EVID1_POPULATION_READINESS_VALUES = {
    "EVID1_POPULATION_READY",
    "EVID1_PARTIALLY_POPULATABLE",
    "EVID1_BLOCKED_SCAFFOLD_ONLY",
    "EVID1_BLOCKED_MISSING_BASELINE_OR_ENRICHED",
    "EVID1_BLOCKED_NO_MEASURABLE_RECORDS",
}


def build_lr6_evid4_emission_review_context(repo_root: str = ".") -> dict[str, Any]:
    return {
        "meta": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "mode": "first_real_evidence_record_emission_review",
            "repo_root": str(Path(repo_root)),
        },
        "basis": {
            "evid1_decision": "BASELINE_OR_ENRICHED_EVIDENCE_MISSING",
            "evid1a_decision": "RUN1_SCAFFOLD_ONLY",
            "evid2_contract": "measurable evidence schema",
            "evid3_contract": "payload-to-evidence-record adapter with scaffold blocking",
        },
    }


def _classify_source_type(path: str) -> str:
    p = path.lower()
    if "baseline" in p and p.endswith(".json"):
        return "baseline replay payload"
    if "enriched" in p and p.endswith(".json"):
        return "enriched replay payload"
    if "lr6_run1" in p:
        return "RUN1 review artifact"
    if "lr6_exp6a" in p:
        return "EXP6A comparison artifact"
    if "lr6_exp6" in p:
        return "EXP6 snapshot artifact"
    if "lr6_exp7" in p:
        return "EXP7 interestingness artifact"
    if "lr6_exp8" in p:
        return "EXP8 findings artifact"
    if p.endswith(".md"):
        return "scaffold-only report"
    return "unknown artifact"


def _replay_phase_for_source_type(source_type: str) -> str:
    mapping = {
        "baseline replay payload": "BASELINE",
        "enriched replay payload": "ENRICHED",
        "RUN1 review artifact": "RUN1_REVIEW",
        "EXP6 snapshot artifact": "EXP6_SNAPSHOT",
        "EXP6A comparison artifact": "EXP6_SNAPSHOT",
        "EXP7 interestingness artifact": "EXP7_INTERESTINGNESS",
        "EXP8 findings artifact": "EXP8_FINDINGS",
    }
    return mapping.get(source_type, "RUN1_REVIEW")


def discover_lr6_evid4_available_payload_sources(repo_root: str = ".") -> list[dict[str, Any]]:
    root = Path(repo_root)
    patterns = [
        "reports/lr6_run1*",
        "reports/lr6_run2_post_wave_evidence_audit.md",
        "reports/lr6_exec2_first_dry_run_execution_review.md",
        "reports/lr6_evid1_pre_post_replay_delta_evidence.md",
        "reports/lr6_evid1a_evidence_source_mapping.md",
        "reports/lr6_evid2_measurable_replay_evidence_capture_design.md",
        "reports/lr6_evid3_measurable_evidence_capture_adapter.md",
        "reports/lr6_exp6*",
        "reports/lr6_exp6a*",
        "reports/lr6_exp7*",
        "reports/lr6_exp8*",
        "**/*lr6*replay*.json",
        "**/*lr6*evidence*.json",
        "**/*lr6*snapshot*.json",
        "**/*lr6*findings*.json",
        "**/*lr6*metadata*.json",
    ]
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for pattern in patterns:
        for m in sorted(root.glob(pattern)):
            if not m.is_file():
                continue
            rel = str(m.relative_to(root))
            if rel in seen:
                continue
            seen.add(rel)
            out.append({"artifact_path": rel, "exists": True, "source_type": _classify_source_type(rel)})
    return sorted(out, key=lambda x: x["artifact_path"])


def build_lr6_evid4_payload_inventory(repo_root: str = ".") -> dict[str, Any]:
    discovered = discover_lr6_evid4_available_payload_sources(repo_root)
    counts: dict[str, int] = {}
    for row in discovered:
        counts[row["source_type"]] = counts.get(row["source_type"], 0) + 1
    return {"total_discovered": len(discovered), "by_source_type": dict(sorted(counts.items())), "sources": discovered}


def _load_payload_or_scaffold(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"payload": data}
        except Exception:
            pass
    return {"review": {"artifact": str(path)}, "narrative": "report_or_non_payload_artifact"}


def emit_lr6_evid4_evidence_records_from_available_payloads(repo_root: str = ".") -> dict[str, Any]:
    root = Path(repo_root)
    inventory = build_lr6_evid4_payload_inventory(repo_root)
    records: list[dict[str, Any]] = []
    for src in inventory["sources"]:
        rel = src["artifact_path"]
        source_type = src["source_type"]
        payload = _load_payload_or_scaffold(root / rel)
        replay_phase = _replay_phase_for_source_type(source_type)
        records.extend(adapt_lr6_evid3_payload_to_evidence_records(payload, replay_phase, rel, SOURCE_PHASE))
    return {"payload_inventory": inventory, "records": records}


def build_lr6_evid4_status_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    by = {s: 0 for s in sorted(EVIDENCE_STATUS_VALUES)}
    for r in records:
        by[r["evidence_status"]] = by.get(r["evidence_status"], 0) + 1
    return {
        "total_records": len(records),
        "status_counts": by,
        "comparison_ready_count": sum(1 for r in records if r["comparison_ready"]),
        "scaffold_only_count": sum(1 for r in records if r["scaffold_only"]),
    }


def build_lr6_evid4_dimension_coverage_review(records: list[dict[str, Any]]) -> dict[str, Any]:
    review: dict[str, Any] = {}
    for dim in EVID1_DIMENSIONS:
        dim_records = [r for r in records if r["metric_dimension"] == dim]
        baseline_records = [r for r in dim_records if r["replay_phase"] == "BASELINE"]
        enriched_records = [r for r in dim_records if r["replay_phase"] == "ENRICHED"]
        measured_count = sum(1 for r in dim_records if r["evidence_status"] == "MEASURED")
        partial_count = sum(1 for r in dim_records if r["evidence_status"] == "PARTIAL")
        scaffold_count = sum(1 for r in dim_records if r["evidence_status"] == "SCAFFOLD_ONLY")
        comparison_ready = any(r["comparison_ready"] for r in baseline_records) and any(r["comparison_ready"] for r in enriched_records)
        blocker = "NONE" if comparison_ready else "missing comparable baseline/enriched measured records"
        review[dim] = {
            "baseline_availability": bool(baseline_records),
            "enriched_availability": bool(enriched_records),
            "measured_record_count": measured_count,
            "partial_record_count": partial_count,
            "scaffold_only_count": scaffold_count,
            "comparison_ready": comparison_ready,
            "blocker": blocker,
        }
    return review


def build_lr6_evid4_scaffold_only_review(records: list[dict[str, Any]]) -> dict[str, Any]:
    scaffold = [r for r in records if r["scaffold_only"]]
    return {"scaffold_only_records": len(scaffold), "scaffold_only_sources": sorted({r["source_artifact"] for r in scaffold})}


def build_lr6_evid4_comparison_readiness_review(records: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [r for r in records if r["comparison_ready"]]
    return {
        "comparison_ready_count": len(ready),
        "comparison_ready_dimensions": sorted({r["metric_dimension"] for r in ready}),
        "blocked_count": len(records) - len(ready),
    }


def build_lr6_evid4_evid1_population_readiness(records: list[dict[str, Any]]) -> str:
    measured = [r for r in records if r["evidence_status"] == "MEASURED"]
    if not measured:
        return "EVID1_BLOCKED_NO_MEASURABLE_RECORDS"
    if any(r["scaffold_only"] for r in records) and not any(r["comparison_ready"] for r in records):
        return "EVID1_BLOCKED_SCAFFOLD_ONLY"
    has_baseline = any(r["replay_phase"] == "BASELINE" and r["evidence_status"] == "MEASURED" for r in records)
    has_enriched = any(r["replay_phase"] == "ENRICHED" and r["evidence_status"] == "MEASURED" for r in records)
    if not (has_baseline and has_enriched):
        return "EVID1_BLOCKED_MISSING_BASELINE_OR_ENRICHED"
    dims_ready = {r["metric_dimension"] for r in records if r["comparison_ready"]}
    if len(dims_ready) == len(EVID1_DIMENSIONS):
        return "EVID1_POPULATION_READY"
    return "EVID1_PARTIALLY_POPULATABLE"


def certify_lr6_evid4_emission_review_boundary() -> dict[str, Any]:
    return {
        "emission_review_only": True,
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


def build_lr6_evid4_supervisor_review(repo_root: str = ".") -> dict[str, Any]:
    context = build_lr6_evid4_emission_review_context(repo_root)
    emission = emit_lr6_evid4_evidence_records_from_available_payloads(repo_root)
    records = emission["records"]
    return {
        "context": context,
        "inspected_payload_sources": emission["payload_inventory"]["sources"],
        "payload_inventory": emission["payload_inventory"],
        "emitted_evidence_record_summary": {"total_records": len(records)},
        "evidence_status_summary": build_lr6_evid4_status_summary(records),
        "dimension_coverage_review": build_lr6_evid4_dimension_coverage_review(records),
        "scaffold_only_review": build_lr6_evid4_scaffold_only_review(records),
        "comparison_readiness_review": build_lr6_evid4_comparison_readiness_review(records),
        "evid1_population_readiness": build_lr6_evid4_evid1_population_readiness(records),
        "boundary_certification": certify_lr6_evid4_emission_review_boundary(),
        "recommendation": "Treat scaffold-only and non-measured artifacts as blocked from EVID1 comparison until baseline+enriched measurable records exist.",
    }


def build_lr6_evid4_markdown_report(repo_root: str = ".") -> str:
    review = build_lr6_evid4_supervisor_review(repo_root)
    return "\n".join([
        "# LR6-EVID4 First Real Evidence Record Emission Review",
        "## objective",
        "Use available local LR6 replay/review artifacts and LR6-EVID3 adapters to emit measurable records without narrative inference.",
        "## inspected payload sources",
        str(review["inspected_payload_sources"]),
        "## payload inventory",
        str(review["payload_inventory"]),
        "## emitted evidence record summary",
        str(review["emitted_evidence_record_summary"]),
        "## evidence status summary",
        str(review["evidence_status_summary"]),
        "## dimension coverage review",
        str(review["dimension_coverage_review"]),
        "## scaffold-only review",
        str(review["scaffold_only_review"]),
        "## comparison readiness review",
        str(review["comparison_readiness_review"]),
        "## EVID1 population readiness",
        str(review["evid1_population_readiness"]),
        "## boundary certification",
        str(review["boundary_certification"]),
        "## recommendation",
        review["recommendation"],
    ])


__all__ = [
    n
    for n in globals()
    if n.startswith("build_lr6_evid4_") or n.startswith("discover_lr6_evid4_") or n.startswith("emit_lr6_evid4_") or n.startswith("certify_lr6_evid4_")
]
