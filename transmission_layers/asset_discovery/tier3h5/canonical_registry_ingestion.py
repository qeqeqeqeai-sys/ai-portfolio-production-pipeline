from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ids import (
    generate_ingestion_run_id,
    generate_issuer_id,
    generate_provenance_id,
    generate_security_id,
)
from transmission_layers.asset_discovery.tier3h5.canonical_registry_models import ProvenanceRecord
from transmission_layers.asset_discovery.tier3h5.canonical_registry_normalization import (
    compute_source_record_hash,
    normalize_exchange_code,
    normalize_issuer_name,
    normalize_ticker,
)
from transmission_layers.asset_discovery.tier3h5.canonical_registry_observability import emit_tier3h5_diagnostics, write_registry_summary
from transmission_layers.asset_discovery.tier3h5.canonical_registry_sample_sources import SAMPLE_REGISTRY_SOURCES

SCHEMA_VERSION = "tier3h5_phase1a_v1"


def run_registry_ingestion(source_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_hashes = [compute_source_record_hash(r) for r in rows]
    source_checksum = hashlib.sha256("".join(sorted(row_hashes)).encode("utf-8")).hexdigest()
    ingestion_run_id = generate_ingestion_run_id(source_name, source_checksum)

    issuer_registry: dict[str, dict[str, Any]] = {}
    security_registry: dict[str, dict[str, Any]] = {}
    seen_hashes: set[str] = set()

    rejected = duplicate = conflicts = id_collisions = normalization_failures = 0

    for row in rows:
        record_hash = compute_source_record_hash(row)
        if record_hash in seen_hashes:
            duplicate += 1
            continue
        seen_hashes.add(record_hash)

        issuer_norm = normalize_issuer_name(row.get("issuer_name"))
        exchange_norm = normalize_exchange_code(row.get("primary_exchange"))
        ticker_norm = normalize_ticker(row.get("ticker"))
        security_type = (row.get("security_type") or "unknown").strip().lower()

        if not issuer_norm or not exchange_norm or not ticker_norm:
            rejected += 1
            normalization_failures += 1
            continue

        issuer_id = generate_issuer_id(issuer_norm, row.get("sec_cik"))
        security_id = generate_security_id(exchange_norm, ticker_norm, security_type)

        issuer_payload = {"issuer_id": issuer_id, "issuer_name_normalized": issuer_norm, "sec_cik": row.get("sec_cik")}
        if issuer_id in issuer_registry and issuer_registry[issuer_id] != issuer_payload:
            conflicts += 1
            id_collisions += 1
            continue
        issuer_registry[issuer_id] = issuer_payload

        security_payload = {"security_id": security_id, "issuer_id": issuer_id, "source_record_hash": record_hash}
        if security_id in security_registry and security_registry[security_id] != security_payload:
            conflicts += 1
            id_collisions += 1
            continue
        security_registry[security_id] = security_payload

    accepted = len(seen_hashes) - rejected - conflicts
    provenance = ProvenanceRecord(
        provenance_id=generate_provenance_id(ingestion_run_id, source_name),
        ingestion_run_id=ingestion_run_id,
        source_name=source_name,
        source_url=rows[0].get("source_url") if rows else None,
        source_retrieved_at=datetime.now(timezone.utc),
        source_checksum=source_checksum,
        source_record_count=len(rows),
        accepted_record_count=max(accepted, 0),
        rejected_record_count=rejected,
        duplicate_record_count=duplicate,
        conflict_record_count=conflicts,
        schema_version=SCHEMA_VERSION,
    )

    summary = {
        "ingestion_run_id": ingestion_run_id,
        "source_name": source_name,
        "records_seen": len(rows),
        "records_accepted": provenance.accepted_record_count,
        "records_rejected": rejected,
        "duplicate_records_detected": duplicate,
        "conflict_records_detected": conflicts,
        "issuer_rows_upserted": len(issuer_registry),
        "security_rows_upserted": len(security_registry),
        "provenance_rows_inserted": 1,
        "deterministic_id_collisions": id_collisions,
        "normalization_failures": normalization_failures,
        "schema_version": SCHEMA_VERSION,
        "status": "success" if rejected == 0 and conflicts == 0 else "completed_with_findings",
    }
    write_registry_summary(summary)
    emit_tier3h5_diagnostics(summary)
    return {"summary": summary, "provenance": provenance, "issuers": issuer_registry, "securities": security_registry}


def run_sample_ingestion() -> dict[str, Any]:
    first_source = next(iter(SAMPLE_REGISTRY_SOURCES.items()))
    return run_registry_ingestion(first_source[0], first_source[1])


if __name__ == "__main__":
    run_sample_ingestion()
