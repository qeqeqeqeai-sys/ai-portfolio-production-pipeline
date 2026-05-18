from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ids import (
    generate_ingestion_run_id,
    generate_issuer_id,
    generate_provenance_id,
    generate_security_id,
)
from transmission_layers.asset_discovery.tier3h5.canonical_registry_models import (
    IngestionRunRecord,
    IssuerRecord,
    ProvenanceRecord,
    SecurityRecord,
)
from transmission_layers.asset_discovery.tier3h5.canonical_registry_normalization import (
    compute_source_record_hash,
    normalize_exchange_code,
    normalize_issuer_name,
    normalize_ticker,
)
from transmission_layers.asset_discovery.tier3h5.canonical_registry_observability import write_registry_summary

SCHEMA_VERSION = "tier3h5_phase1a_v1"

SAMPLE_REGISTRY_SOURCES: dict[str, list[dict[str, Any]]] = {
    "sec_issuer_fixture": [
        {
            "source_url": "file://fixtures/tier3h5_sec_issuer_fixture.json",
            "issuer_name": "Example Holdings Inc.",
            "country_code": "US",
            "primary_exchange": "NASDAQ",
            "ticker": "EXM",
            "issuer_type": "operating_company",
            "sec_cik": "0001234567",
            "lei": "5493001KJTIIGC8Y1R12",
            "security_name": "Example Holdings Common Stock",
            "security_type": "common_stock",
            "share_class": "A",
            "currency": "USD",
            "listing_status": "active",
            "is_primary_listing": True,
        }
    ],
    "nasdaq_listing_fixture": [
        {
            "source_url": "file://fixtures/tier3h5_nasdaq_listing_fixture.json",
            "issuer_name": "Example Holdings Inc",
            "country_code": "US",
            "primary_exchange": "nasdaq",
            "ticker": " exm ",
            "issuer_type": "operating_company",
            "sec_cik": "0001234567",
            "lei": "5493001KJTIIGC8Y1R12",
            "security_name": "Example Holdings Common Stock",
            "security_type": "common_stock",
            "share_class": "A",
            "currency": "USD",
            "listing_status": "active",
            "is_primary_listing": True,
        }
    ],
    "nyse_listing_fixture": [
        {
            "source_url": "file://fixtures/tier3h5_nyse_listing_fixture.json",
            "issuer_name": "Example Holdings Inc.",
            "country_code": "US",
            "primary_exchange": "NYSE",
            "ticker": "EXM",
            "issuer_type": "operating_company",
            "sec_cik": "0001234567",
            "security_name": "Example Holdings Depositary Shares",
            "security_type": "preferred_stock",
            "share_class": "P",
            "currency": "USD",
            "listing_status": "active",
            "is_primary_listing": False,
        }
    ],
}


def run_registry_ingestion(source_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    all_hashes = [compute_source_record_hash(row) for row in rows]
    source_checksum = hashlib.sha256("".join(sorted(all_hashes)).encode("utf-8")).hexdigest()
    ingestion_run_id = generate_ingestion_run_id(source_name, source_checksum)

    issuer_registry: dict[str, IssuerRecord] = {}
    security_registry: dict[str, SecurityRecord] = {}
    seen_hashes: set[str] = set()

    rejected = duplicates = conflicts = id_collisions = normalization_failures = 0

    for row in rows:
        row_hash = compute_source_record_hash(row)
        if row_hash in seen_hashes:
            duplicates += 1
            continue
        seen_hashes.add(row_hash)

        issuer_name_canonical = (row.get("issuer_name") or "").strip()
        issuer_name_normalized = normalize_issuer_name(issuer_name_canonical)
        exchange_raw = (row.get("primary_exchange") or "").strip()
        normalized_exchange = normalize_exchange_code(exchange_raw)
        ticker_raw = row.get("ticker")
        normalized_ticker = normalize_ticker(ticker_raw)
        security_type = (row.get("security_type") or "unknown").strip().lower()

        if not issuer_name_normalized or not normalized_ticker:
            rejected += 1
            normalization_failures += 1
            continue

        issuer_id = generate_issuer_id(issuer_name_normalized, row.get("sec_cik"))
        security_id = generate_security_id(normalized_exchange, normalized_ticker, security_type)

        issuer_record = IssuerRecord(
            issuer_id=issuer_id,
            issuer_name_canonical=issuer_name_canonical,
            issuer_name_normalized=issuer_name_normalized,
            country_code=row.get("country_code"),
            primary_exchange=exchange_raw,
            primary_ticker=(ticker_raw or "").strip() or None,
            issuer_type=row.get("issuer_type"),
            sec_cik=row.get("sec_cik"),
            lei=row.get("lei"),
            issuer_status=row.get("issuer_status") or "active",
            source_authority=source_name,
        )
        if issuer_id in issuer_registry and issuer_registry[issuer_id] != issuer_record:
            conflicts += 1
            id_collisions += 1
            continue
        issuer_registry[issuer_id] = issuer_record

        security_record = SecurityRecord(
            security_id=security_id,
            issuer_id=issuer_id,
            ticker=(ticker_raw or "").strip(),
            normalized_ticker=normalized_ticker,
            exchange=exchange_raw,
            normalized_exchange=normalized_exchange,
            security_name=row.get("security_name"),
            security_type=security_type,
            share_class=row.get("share_class"),
            currency=row.get("currency"),
            listing_status=row.get("listing_status") or "active",
            is_primary_listing=bool(row.get("is_primary_listing", False)),
            source_registry=source_name,
            source_record_hash=row_hash,
        )
        if security_id in security_registry and security_registry[security_id] != security_record:
            conflicts += 1
            id_collisions += 1
            continue
        security_registry[security_id] = security_record

    accepted = len(seen_hashes) - rejected - duplicates - conflicts
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
        duplicate_record_count=duplicates,
        conflict_record_count=conflicts,
        schema_version=SCHEMA_VERSION,
    )
    ingestion_run = IngestionRunRecord(
        ingestion_run_id=ingestion_run_id,
        source_name=source_name,
        source_checksum=source_checksum,
        schema_version=SCHEMA_VERSION,
        status="success" if rejected == 0 and conflicts == 0 else "completed_with_findings",
    )

    summary = {
        "ingestion_run_id": ingestion_run_id,
        "source_name": source_name,
        "records_seen": len(rows),
        "records_accepted": provenance.accepted_record_count,
        "records_rejected": rejected,
        "duplicate_records_detected": duplicates,
        "conflict_records_detected": conflicts,
        "issuer_rows_upserted": len(issuer_registry),
        "security_rows_upserted": len(security_registry),
        "provenance_rows_inserted": 1,
        "deterministic_id_collisions": id_collisions,
        "normalization_failures": normalization_failures,
        "schema_version": SCHEMA_VERSION,
        "status": ingestion_run.status,
    }
    write_registry_summary(summary)
    return {
        "ingestion_run": ingestion_run,
        "issuers": issuer_registry,
        "securities": security_registry,
        "provenance": provenance,
        "summary": summary,
        "raw_summary_json": json.dumps(summary, sort_keys=True),
    }
