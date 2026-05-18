from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

PHASE = "tier3h5_phase2b"
PHASE_VERSION = "tier3h5_phase2b_1"
LOG_DIR = Path("logs")
FRESHNESS_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_freshness_summary.json"
QUALITY_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_quality_summary.json"
LINEAGE_PATH = LOG_DIR / "tier3h5_registry_snapshot_lineage.json"
PRECEDENCE_PATH = LOG_DIR / "tier3h5_source_precedence_diagnostics.json"
PHASE_SUMMARY_PATH = LOG_DIR / "tier3h5_phase2b_quality_freshness_summary.json"
FOUNDATION_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_foundation_summary.json"
RESOLUTION_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_resolution_summary.json"
ADVISORY_SUMMARY_PATH = LOG_DIR / "tier3h5_advisory_registry_summary.json"
PROPAGATION_SUMMARY_PATH = LOG_DIR / "tier3h5_registry_propagation_governance_summary.json"

FRESH_DAYS_MAX = 30
AGING_DAYS_MAX = 90

DUPLICATE_DENSITY_HIGH = 0.10
CONFLICT_DENSITY_HIGH = 0.05
UNRESOLVED_DENSITY_HIGH = 0.05
NORMALIZATION_FAILURE_DENSITY_HIGH = 0.03

SOURCE_PRECEDENCE_ORDER = ["exchange_primary", "listing_primary", "vendor_secondary", "vendor_tertiary"]


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_provenance_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": row.get("source_name"),
        "source_dataset_version": row.get("source_dataset_version"),
        "registry_snapshot_id": row.get("registry_snapshot_id"),
        "registry_effective_date": row.get("registry_effective_date"),
        "ingestion_run_id": row.get("ingestion_run_id"),
        "registry_region": row.get("registry_region"),
        "exchange_source": row.get("exchange_source"),
        "listing_source": row.get("listing_source"),
        "normalization_version": row.get("normalization_version"),
        "source_record_count": _safe_int(row.get("source_record_count", row.get("records_seen"))),
        "accepted_record_count": _safe_int(row.get("accepted_record_count", row.get("records_accepted"))),
        "rejected_record_count": _safe_int(row.get("rejected_record_count", row.get("records_rejected"))),
        "duplicate_record_count": _safe_int(row.get("duplicate_record_count", row.get("duplicates", row.get("duplicate_records_detected")))),
        "conflict_record_count": _safe_int(row.get("conflict_record_count", row.get("conflicts", row.get("conflict_records_detected")))),
        "deterministic_id_collisions": _safe_int(row.get("deterministic_id_collisions")),
        "normalization_failures": _safe_int(row.get("normalization_failures")),
    }


def load_phase2b_provenance_inputs(provenance_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    foundation = _load_json(FOUNDATION_SUMMARY_PATH)
    resolution = _load_json(RESOLUTION_SUMMARY_PATH)
    advisory = _load_json(ADVISORY_SUMMARY_PATH)
    propagation = _load_json(PROPAGATION_SUMMARY_PATH)

    rows = [_normalize_provenance_row(r) for r in (provenance_rows or [])]
    if not rows and foundation:
        rows = [_normalize_provenance_row(foundation)]

    return {
        "provenance_rows": rows,
        "foundation_summary": foundation,
        "resolution_summary": resolution,
        "advisory_summary": advisory,
        "propagation_summary": propagation,
    }


def _parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return parsed.date()


def classify_freshness(age_days: int | None) -> str:
    if age_days is None:
        return "unknown_freshness"
    if age_days <= FRESH_DAYS_MAX:
        return "fresh"
    if age_days <= AGING_DAYS_MAX:
        return "aging"
    return "stale"


def summarize_registry_freshness(provenance_rows: list[dict[str, Any]], as_of_date: date | None = None) -> dict[str, Any]:
    as_of = as_of_date or date.today()
    freshness_status_counts: Counter[str] = Counter()
    ages_by_source: dict[str, int | None] = {}
    stale_sources: list[str] = []
    missing_effective_date_count = 0
    missing_dataset_version_count = 0
    missing_snapshot_id_count = 0

    for row in provenance_rows:
        source_name = str(row.get("source_name") or "unknown_source")
        effective_date = row.get("registry_effective_date")
        if not effective_date:
            missing_effective_date_count += 1
        if not row.get("source_dataset_version"):
            missing_dataset_version_count += 1
        if not row.get("registry_snapshot_id"):
            missing_snapshot_id_count += 1

        age_days = None
        parsed_date = _parse_iso_date(effective_date) if effective_date else None
        if parsed_date:
            age_days = (as_of - parsed_date).days
        status = classify_freshness(age_days)
        freshness_status_counts[status] += 1
        ages_by_source[source_name] = age_days
        if status == "stale":
            stale_sources.append(source_name)

    return {
        "phase": PHASE,
        "status": "success",
        "deterministic_thresholds": {"fresh_days_max": FRESH_DAYS_MAX, "aging_days_max": AGING_DAYS_MAX},
        "registry_sources_seen": len({str(r.get('source_name') or 'unknown_source') for r in provenance_rows}),
        "stale_registry_sources": sorted(set(stale_sources)),
        "stale_registry_source_count": len(set(stale_sources)),
        "missing_effective_date_count": missing_effective_date_count,
        "missing_dataset_version_count": missing_dataset_version_count,
        "missing_snapshot_id_count": missing_snapshot_id_count,
        "registry_age_days_by_source": ages_by_source,
        "registry_freshness_status_counts": dict(sorted(freshness_status_counts.items())),
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator > 0 else 0.0


def classify_quality_status(row: dict[str, Any]) -> str:
    if row["records_seen"] <= 0:
        return "unknown_quality"
    if row["provenance_completeness_ratio"] < 1.0:
        return "incomplete_provenance"
    if row["duplicate_density"] > DUPLICATE_DENSITY_HIGH:
        return "high_duplicate_density"
    if row["conflict_density"] > CONFLICT_DENSITY_HIGH:
        return "high_conflict_density"
    if row["unresolved_density"] > UNRESOLVED_DENSITY_HIGH:
        return "high_unresolved_density"
    if row["normalization_failure_density"] > NORMALIZATION_FAILURE_DENSITY_HIGH:
        return "normalization_issues"
    return "complete"


def summarize_registry_quality(provenance_rows: list[dict[str, Any]], resolution_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    resolution_summary = resolution_summary or {}
    per_source: list[dict[str, Any]] = []
    quality_counter: Counter[str] = Counter()

    attempts = _safe_int(resolution_summary.get("registry_resolution_attempts"))
    unresolved_count = _safe_int(resolution_summary.get("registry_resolution_no_match")) + _safe_int(
        resolution_summary.get("registry_resolution_invalid_input")
    )

    for row in provenance_rows:
        seen = _safe_int(row.get("source_record_count"))
        rejected = _safe_int(row.get("rejected_record_count"))
        duplicates = _safe_int(row.get("duplicate_record_count"))
        conflicts = _safe_int(row.get("conflict_record_count"))
        normalization_failures = _safe_int(row.get("normalization_failures")) or max(0, rejected - duplicates - conflicts)

        present = sum(1 for f in ("source_dataset_version", "registry_snapshot_id", "registry_effective_date", "ingestion_run_id") if row.get(f))
        out = {
            "source_name": row.get("source_name"),
            "source_dataset_version": row.get("source_dataset_version"),
            "registry_region": row.get("registry_region"),
            "exchange_source": row.get("exchange_source"),
            "listing_source": row.get("listing_source"),
            "records_seen": seen,
            "provenance_completeness_ratio": round(present / 4.0, 6),
            "duplicate_density": _ratio(duplicates, seen),
            "conflict_density": _ratio(conflicts, seen),
            "unresolved_density": _ratio(unresolved_count, max(seen, attempts)),
            "normalization_failure_density": _ratio(normalization_failures, seen),
        }
        out["quality_status"] = classify_quality_status(out)
        quality_counter[out["quality_status"]] += 1
        per_source.append(out)

    total_seen = sum(_safe_int(r.get("source_record_count")) for r in provenance_rows)
    return {
        "phase": PHASE,
        "status": "success",
        "registry_sources_seen": len(per_source),
        "provenance_completeness_ratio": round(sum(r["provenance_completeness_ratio"] for r in per_source) / len(per_source), 6) if per_source else 0.0,
        "duplicate_density": _ratio(sum(_safe_int(r.get("duplicate_record_count")) for r in provenance_rows), total_seen),
        "conflict_density": _ratio(sum(_safe_int(r.get("conflict_record_count")) for r in provenance_rows), total_seen),
        "unresolved_density": _ratio(unresolved_count, attempts),
        "normalization_failure_density": _ratio(sum(_safe_int(r.get("normalization_failures")) for r in provenance_rows), total_seen),
        "deterministic_thresholds": {
            "duplicate_density_high": DUPLICATE_DENSITY_HIGH,
            "conflict_density_high": CONFLICT_DENSITY_HIGH,
            "unresolved_density_high": UNRESOLVED_DENSITY_HIGH,
            "normalization_failure_density_high": NORMALIZATION_FAILURE_DENSITY_HIGH,
        },
        "registry_quality_status_counts": dict(sorted(quality_counter.items())),
        "source_quality_breakdown": per_source,
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }


def summarize_snapshot_lineage(provenance_rows: list[dict[str, Any]]) -> dict[str, Any]:
    lineage = []
    for row in provenance_rows:
        rejected = _safe_int(row.get("rejected_record_count"))
        duplicates = _safe_int(row.get("duplicate_record_count"))
        conflicts = _safe_int(row.get("conflict_record_count"))
        normalization_failures = _safe_int(row.get("normalization_failures")) or max(0, rejected - duplicates - conflicts)
        lineage.append(
            {
                "registry_snapshot_id": row.get("registry_snapshot_id"),
                "source_name": row.get("source_name"),
                "source_dataset_version": row.get("source_dataset_version"),
                "registry_effective_date": row.get("registry_effective_date"),
                "ingestion_run_id": row.get("ingestion_run_id"),
                "registry_region": row.get("registry_region"),
                "exchange_source": row.get("exchange_source"),
                "listing_source": row.get("listing_source"),
                "normalization_version": row.get("normalization_version"),
                "records_seen": _safe_int(row.get("source_record_count")),
                "records_accepted": _safe_int(row.get("accepted_record_count")),
                "records_rejected": rejected,
                "duplicates": duplicates,
                "conflicts": conflicts,
                "normalization_failures": normalization_failures,
                "deterministic_id_collisions": _safe_int(row.get("deterministic_id_collisions")),
            }
        )
    return {"phase": PHASE, "status": "success", "lineage": lineage, "enforcement_enabled": False, "canonical_override_enabled": False}


def summarize_source_precedence() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "status": "success",
        "source_precedence_mode": "advisory_only",
        "configured_source_precedence": SOURCE_PRECEDENCE_ORDER,
        "source_precedence_applied": False,
        "notes": "Source precedence is advisory visibility only; no resolution outcomes are mutated.",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_phase2b_quality_freshness_governance(provenance_rows: list[dict[str, Any]] | None = None, as_of_date: date | None = None) -> dict[str, Any]:
    inputs = load_phase2b_provenance_inputs(provenance_rows)
    rows = inputs["provenance_rows"]
    freshness = summarize_registry_freshness(rows, as_of_date=as_of_date)
    quality = summarize_registry_quality(rows, resolution_summary=inputs.get("resolution_summary"))
    lineage = summarize_snapshot_lineage(rows)
    precedence = summarize_source_precedence()

    summary = {
        "phase": PHASE_VERSION,
        "status": "success",
        "registry_sources_seen": freshness["registry_sources_seen"],
        "freshness_status_counts": freshness["registry_freshness_status_counts"],
        "quality_status_counts": quality["registry_quality_status_counts"],
        "stale_registry_source_count": freshness["stale_registry_source_count"],
        "missing_provenance_field_counts": {
            "missing_effective_date_count": freshness["missing_effective_date_count"],
            "missing_dataset_version_count": freshness["missing_dataset_version_count"],
            "missing_snapshot_id_count": freshness["missing_snapshot_id_count"],
        },
        "source_precedence_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
        "provenance_backed_population_enabled": True,
    }

    _write_json(FRESHNESS_SUMMARY_PATH, freshness)
    _write_json(QUALITY_SUMMARY_PATH, quality)
    _write_json(LINEAGE_PATH, lineage)
    _write_json(PRECEDENCE_PATH, precedence)
    _write_json(PHASE_SUMMARY_PATH, summary)
    return summary


if __name__ == "__main__":
    run_phase2b_quality_freshness_governance()
