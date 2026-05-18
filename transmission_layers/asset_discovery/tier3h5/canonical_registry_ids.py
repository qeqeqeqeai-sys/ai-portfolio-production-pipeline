from __future__ import annotations

import hashlib


def _stable_digest(parts: tuple[str, ...]) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]


def generate_issuer_id(normalized_issuer_name: str, sec_cik: str | None = None) -> str:
    cik = (sec_cik or "").strip()
    return f"iss_{_stable_digest((normalized_issuer_name, cik))}"


def generate_security_id(normalized_exchange: str, normalized_ticker: str, security_type: str) -> str:
    return f"sec_{_stable_digest((normalized_exchange, normalized_ticker, security_type.strip().lower()))}"


def generate_ingestion_run_id(source_name: str, source_checksum: str) -> str:
    return f"ing_{_stable_digest((source_name, source_checksum))}"


def generate_provenance_id(ingestion_run_id: str, source_name: str) -> str:
    return f"prov_{_stable_digest((ingestion_run_id, source_name))}"
