from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class IssuerRecord:
    issuer_id: str
    issuer_name_canonical: str
    issuer_name_normalized: str
    country_code: str | None = None
    primary_exchange: str | None = None
    primary_ticker: str | None = None
    issuer_type: str | None = None
    sec_cik: str | None = None
    lei: str | None = None
    status: str = "active"


@dataclass(frozen=True)
class SecurityRecord:
    security_id: str
    issuer_id: str
    ticker: str
    exchange: str
    security_name: str | None
    security_type: str
    share_class: str | None = None
    currency: str | None = None
    listing_status: str = "active"
    is_primary_listing: bool = False
    source_registry: str = "fixture"
    source_record_hash: str = ""


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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
