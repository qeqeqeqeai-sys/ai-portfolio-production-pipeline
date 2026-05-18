from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from transmission_layers.asset_discovery.tier3h5.canonical_registry_models import IssuerRecord, ProvenanceRecord, SecurityRecord
from transmission_layers.asset_discovery.tier3h5.registry_observability import write_registry_summary

SCHEMA_VERSION = "tier3h5_phase1a_v1"


def normalize_exchange_code(value: str | None) -> str:
    if not value:
        return "UNKNOWN"
    clean = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    return clean or "UNKNOWN"


def normalize_ticker(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", "", value).upper()


def normalize_issuer_name(value: str | None) -> str:
    if not value:
        return ""
    normalized = re.sub(r"[^A-Za-z0-9 ]", " ", value).upper()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def compute_source_record_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _deterministic_id(prefix: str, key: str) -> str:
    return f"{prefix}_{hashlib.sha256(key.encode('utf-8')).hexdigest()[:20]}"


def run_registry_ingestion(source_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    ingestion_run_id = _deterministic_id("ing", f"{source_name}:{len(rows)}")
    issuer_registry: dict[str, IssuerRecord] = {}
    security_registry: dict[str, SecurityRecord] = {}
    seen_hashes: set[str] = set()
    seen_canonical_keys: set[str] = set()

    rejected = duplicates = conflicts = id_collisions = 0

    for row in rows:
        record_hash = compute_source_record_hash(row)
        if record_hash in seen_hashes:
            duplicates += 1
            continue
        seen_hashes.add(record_hash)

        issuer_name_norm = normalize_issuer_name(row.get("issuer_name"))
        ticker_norm = normalize_ticker(row.get("ticker"))
        exchange_norm = normalize_exchange_code(row.get("primary_exchange"))
        security_type = (row.get("security_type") or "unknown").strip().lower()

        if not issuer_name_norm or not ticker_norm:
            rejected += 1
            continue

        canonical_row_key = f"{issuer_name_norm}|{exchange_norm}|{ticker_norm}|{security_type}|{source_name}"
        if canonical_row_key in seen_canonical_keys:
            duplicates += 1
            continue
        seen_canonical_keys.add(canonical_row_key)

        issuer_authority_key = f"{issuer_name_norm}|{row.get('sec_cik') or ''}|{row.get('lei') or ''}"
        issuer_id = _deterministic_id("iss", issuer_authority_key)
        security_id = _deterministic_id("sec", f"{exchange_norm}|{ticker_norm}|{security_type}|{source_name}")

        issuer = IssuerRecord(
            issuer_id=issuer_id,
            issuer_name_canonical=(row.get("issuer_name") or "").strip(),
            issuer_name_normalized=issuer_name_norm,
            country_code=row.get("country_code"),
            primary_exchange=exchange_norm,
            primary_ticker=ticker_norm,
            issuer_type=row.get("issuer_type"),
            sec_cik=row.get("sec_cik"),
            lei=row.get("lei"),
        )
        if issuer_id in issuer_registry and issuer_registry[issuer_id] != issuer:
            conflicts += 1
            id_collisions += 1
            continue
        issuer_registry[issuer_id] = issuer

        security = SecurityRecord(
            security_id=security_id,
            issuer_id=issuer_id,
            ticker=ticker_norm,
            exchange=exchange_norm,
            security_name=row.get("security_name"),
            security_type=security_type,
            share_class=row.get("share_class"),
            currency=row.get("currency"),
            listing_status=row.get("listing_status") or "active",
            is_primary_listing=bool(row.get("is_primary_listing", False)),
            source_registry=source_name,
            source_record_hash=record_hash,
        )
        if security_id in security_registry and security_registry[security_id] != security:
            conflicts += 1
            id_collisions += 1
            continue
        security_registry[security_id] = security

    provenance = ProvenanceRecord(
        provenance_id=_deterministic_id("prov", ingestion_run_id),
        ingestion_run_id=ingestion_run_id,
        source_name=source_name,
        source_url=rows[0].get("source_url") if rows else None,
        source_retrieved_at=datetime.now(timezone.utc),
        source_checksum=hashlib.sha256("".join(sorted(seen_hashes)).encode("utf-8")).hexdigest(),
        source_record_count=len(rows),
        accepted_record_count=len(seen_hashes) - rejected - duplicates,
        rejected_record_count=rejected,
        duplicate_record_count=duplicates,
        conflict_record_count=conflicts,
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
        "schema_version": SCHEMA_VERSION,
        "status": "success" if rejected == 0 and conflicts == 0 else "completed_with_findings",
    }
    write_registry_summary(summary)
    return {
        "issuers": issuer_registry,
        "securities": security_registry,
        "provenance": provenance,
        "summary": summary,
    }
