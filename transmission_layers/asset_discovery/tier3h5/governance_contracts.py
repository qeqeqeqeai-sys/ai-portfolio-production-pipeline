from __future__ import annotations

from typing import Any

SUPPORTED_EXCHANGES = {"NYSE", "NASDAQ", "ARCA", "TSX", "LSE", "HKEX", "SGX"}
SUPPORTED_SECURITY_TYPES = {"equity", "etf", "adr", "reit", "preferred_share", "warrant", "unit"}

GOVERNANCE_STATUS_UNRESOLVED_CROSS_REGISTRY = "unresolved_cross_registry"
GOVERNANCE_STATUS_CONFLICTING_CROSS_REGISTRY = "conflicting_cross_registry"
GOVERNANCE_STATUS_DUAL_LISTING_CONFIRMED = "dual_listing_confirmed"
GOVERNANCE_STATUS_DETERMINISTIC_ALIAS = "deterministic_alias"
GOVERNANCE_STATUS_CANONICAL_PRIMARY = "canonical_primary"

EDGE_TYPE_ISSUER_SECURITY = "issuer_security"
EDGE_TYPE_ALIAS = "alias"
EDGE_TYPE_DUAL_LISTING = "dual_listing"

IDENTITY_MODE_DETERMINISTIC_EXACT_MATCH = "deterministic_exact_match"
LINEAGE_SCOPE_CROSS_REGISTRY = "cross_registry"
LINKAGE_MODE_DETERMINISTIC_EXACT_MATCH_ONLY = "deterministic_exact_match_only"

ENFORCEMENT_ENABLED_DEFAULT = False
CANONICAL_OVERRIDE_ENABLED_DEFAULT = False
REPLAY_SAFE_LINEAGE_ENABLED_DEFAULT = True


def is_supported_exchange(exchange: str | None) -> bool:
    return str(exchange or "").strip().upper() in SUPPORTED_EXCHANGES


def is_supported_security_type(security_type: str | None) -> bool:
    return str(security_type or "").strip().lower() in SUPPORTED_SECURITY_TYPES


def classify_registry_candidate(exchange: str | None, security_type: str | None) -> dict[str, Any]:
    exchange_normalized = str(exchange or "").strip().upper()
    security_type_normalized = str(security_type or "").strip().lower()
    exchange_supported = exchange_normalized in SUPPORTED_EXCHANGES
    security_type_supported = security_type_normalized in SUPPORTED_SECURITY_TYPES
    return {
        "exchange": exchange_normalized or None,
        "security_type": security_type_normalized or None,
        "exchange_supported": exchange_supported,
        "security_type_supported": security_type_supported,
        "is_supported_candidate": exchange_supported and security_type_supported,
    }


def governance_policy_summary() -> dict[str, Any]:
    return {
        "supported_exchanges": sorted(SUPPORTED_EXCHANGES),
        "supported_security_types": sorted(SUPPORTED_SECURITY_TYPES),
        "linkage_mode": LINKAGE_MODE_DETERMINISTIC_EXACT_MATCH_ONLY,
        "lineage_scope": LINEAGE_SCOPE_CROSS_REGISTRY,
        "identity_mode": IDENTITY_MODE_DETERMINISTIC_EXACT_MATCH,
        "enforcement_enabled": ENFORCEMENT_ENABLED_DEFAULT,
        "canonical_override_enabled": CANONICAL_OVERRIDE_ENABLED_DEFAULT,
        "replay_safe_lineage_enabled": REPLAY_SAFE_LINEAGE_ENABLED_DEFAULT,
    }
