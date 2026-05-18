"""Tier 3H.5 canonical registry foundation package exports."""

SCHEMA_VERSION = "tier3h5_phase1a_v1"

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ids import generate_issuer_id, generate_security_id
from transmission_layers.asset_discovery.tier3h5.canonical_registry_ingestion import SAMPLE_REGISTRY_SOURCES, run_registry_ingestion
from transmission_layers.asset_discovery.tier3h5.canonical_registry_normalization import (
    compute_source_record_hash,
    normalize_exchange_code,
    normalize_issuer_name,
    normalize_ticker,
)

__all__ = [
    "normalize_exchange_code",
    "normalize_ticker",
    "normalize_issuer_name",
    "compute_source_record_hash",
    "generate_issuer_id",
    "generate_security_id",
    "SAMPLE_REGISTRY_SOURCES",
    "run_registry_ingestion",
]
