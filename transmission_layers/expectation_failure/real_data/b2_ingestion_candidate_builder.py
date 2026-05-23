"""B2 deterministic ingestion candidate envelope builder."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json


FORBIDDEN_CAPABILITIES = (
    "trading",
    "prediction",
    "optimization",
    "target_prices",
    "portfolio_allocation",
    "autonomous_api_fetching",
    "autonomous_writes",
    "adaptive_learning",
    "unrestricted_llm_reasoning",
)


def _checksum(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_ingestion_candidate(
    accepted_records: list[dict],
    quarantined_records: list[dict],
    entity_symbols: tuple[str, ...],
    benchmark_symbols: tuple[str, ...],
    as_of_date: str,
) -> dict:
    accepted = deepcopy(accepted_records)
    quarantined = deepcopy(quarantined_records)

    accepted_symbols = {r["symbol"] for r in accepted}
    accepted_metrics = {r["metric_name"] for r in accepted}

    entity_covered = sorted([s for s in entity_symbols if s in accepted_symbols])
    benchmark_covered = sorted([s for s in benchmark_symbols if s in accepted_symbols])
    stale_count = sum(1 for q in quarantined if q["reason_code"] == "stale_source_timestamp")

    degraded_flags = sorted(
        {
            "quarantine_present" if quarantined else "",
            "stale_inputs_present" if stale_count else "",
            "entity_coverage_incomplete" if len(entity_covered) != len(entity_symbols) else "",
            "benchmark_coverage_incomplete" if len(benchmark_covered) != len(benchmark_symbols) else "",
        }
        - {""}
    )

    envelope = {
        "snapshot_stage": "B2_CONTROLLED_MARKET_INGESTION_CANDIDATE",
        "as_of_date": as_of_date,
        "accepted_records": accepted,
        "quarantined_records": quarantined,
        "entity_coverage_summary": {
            "covered_symbols": entity_covered,
            "missing_symbols": sorted([s for s in entity_symbols if s not in accepted_symbols]),
        },
        "benchmark_coverage_summary": {
            "covered_symbols": benchmark_covered,
            "missing_symbols": sorted([s for s in benchmark_symbols if s not in accepted_symbols]),
        },
        "metric_coverage_summary": {
            "covered_metrics": sorted(accepted_metrics),
            "record_count": len(accepted),
        },
        "freshness_summary": {
            "stale_record_quarantine_count": stale_count,
            "as_of_date": as_of_date,
        },
        "degraded_input_flags": degraded_flags,
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
        "operating_constraints": {
            "network_calls": "none",
            "database_writes": "none",
            "symbol_source": "b1_fixed_registries_only",
            "input_mutation": "disallowed",
        },
    }
    envelope["deterministic_checksum"] = _checksum(envelope)
    envelope["certification_status"] = "PENDING_B2_CERTIFICATION"
    return envelope
