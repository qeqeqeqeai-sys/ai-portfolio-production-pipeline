from __future__ import annotations

import hashlib


def _digest(prefix: str, components: list[str]) -> str:
    canonical = "|".join([c.strip().upper() for c in components])
    return f"{prefix}_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def generate_issuer_id(issuer_name_normalized: str, sec_cik: str | None = None) -> str:
    return _digest("iss", [issuer_name_normalized, sec_cik or ""]) 


def generate_security_id(normalized_exchange: str, normalized_ticker: str, security_type: str) -> str:
    return _digest("sec", [normalized_exchange, normalized_ticker, security_type])


def generate_ingestion_run_id(source_name: str, source_checksum: str) -> str:
    return _digest("run", [source_name, source_checksum])


def generate_provenance_id(ingestion_run_id: str, source_name: str) -> str:
    return _digest("prv", [ingestion_run_id, source_name])
