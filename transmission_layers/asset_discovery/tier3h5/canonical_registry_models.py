from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IssuerRecord:
    issuer_id: str
    issuer_name_canonical: str
    issuer_name_normalized: str
    country_code: str | None
    primary_exchange: str | None
    primary_ticker: str | None
    issuer_type: str | None
    sec_cik: str | None
    lei: str | None


@dataclass(frozen=True)
class SecurityRecord:
    security_id: str
    issuer_id: str
    ticker: str
    normalized_ticker: str
    exchange: str
    normalized_exchange: str
    security_name: str | None
    security_type: str
    currency: str | None
    source_record_hash: str


@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    ingestion_run_id: str
    source_name: str
    source_url: str | None
    source_retrieved_at: datetime
    source_checksum: str
    source_record_count: int
    accepted_record_count: int
    rejected_record_count: int
    duplicate_record_count: int
    conflict_record_count: int
    schema_version: str
