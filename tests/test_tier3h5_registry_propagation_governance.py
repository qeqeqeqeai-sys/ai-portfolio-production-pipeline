import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.advisory_registry_hooks import enrich_propagation_identities


REGISTRY = [
    {"security_id": "sec_aapl_eq", "issuer_id": "iss_aapl", "ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity", "is_active": True, "source_name": "canon"},
    {"security_id": "sec_msft_eq", "issuer_id": "iss_msft", "ticker": "MSFT", "exchange": "NASDAQ", "security_type": "equity", "is_active": True, "source_name": "canon"},
    {"security_id": None, "issuer_id": "iss_ibm", "ticker": "IBM", "exchange": "NYSE", "security_type": "equity", "is_active": True, "source_name": "canon"},
    {"security_id": "sec_conflict_1", "issuer_id": "iss_conflict", "ticker": "CON", "exchange": "NASDAQ", "security_type": "equity", "is_active": True},
    {"security_id": "sec_conflict_2", "issuer_id": "iss_conflict", "ticker": "CON", "exchange": "NASDAQ", "security_type": "equity", "is_active": True},
]


def test_accepted_security_match_creates_canonical_id() -> None:
    out = enrich_propagation_identities([{"candidate_asset_id": "x1", "ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity"}], REGISTRY)
    row = out["enriched_candidates"][0]
    assert row["canonical_propagation_asset_id"] == "CANONICAL_SECURITY::sec_aapl_eq"
    assert row["propagation_identity_mode"] == "canonical_registry_security"


def test_accepted_issuer_only_match_creates_issuer_level_canonical_id() -> None:
    out = enrich_propagation_identities([{"candidate_asset_id": "x1", "ticker": "IBM", "exchange": "NYSE", "security_type": "equity"}], REGISTRY)
    row = out["enriched_candidates"][0]
    assert row["canonical_propagation_asset_id"] == "CANONICAL_ISSUER::iss_ibm"
    assert row["propagation_identity_mode"] == "canonical_registry_issuer"


def test_no_match_preserves_legacy_candidate_id() -> None:
    out = enrich_propagation_identities([{"candidate_asset_id": "legacy", "ticker": "ZZZZ", "exchange": "NASDAQ"}], REGISTRY)
    row = out["enriched_candidates"][0]
    assert row["candidate_asset_id"] == "legacy"
    assert row["propagation_identity_mode"] == "unresolved"


def test_conflict_preserves_legacy_and_records_status() -> None:
    out = enrich_propagation_identities([{"candidate_asset_id": "legacy", "ticker": "CON", "exchange": "NASDAQ", "security_type": "equity"}], REGISTRY)
    row = out["enriched_candidates"][0]
    assert row["registry_resolution_status"] == "conflict"
    assert row["propagation_identity_mode"] == "conflict_preserved_legacy"


def test_invalid_input_preserves_legacy_behavior() -> None:
    out = enrich_propagation_identities([{"candidate_asset_id": "legacy", "ticker": "", "exchange": "NASDAQ"}], REGISTRY)
    row = out["enriched_candidates"][0]
    assert row["registry_resolution_status"] == "invalid_input"
    assert row["propagation_identity_mode"] == "invalid_input_preserved_legacy"


def test_duplicate_legacy_candidates_collapse_deterministically() -> None:
    candidates = [
        {"candidate_asset_id": "legacy_1", "ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity"},
        {"candidate_asset_id": "legacy_2", "ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity"},
    ]
    out = enrich_propagation_identities(candidates, REGISTRY)
    assert len(out["enriched_candidates"]) == 1
    assert out["diagnostics"]["duplicate_legacy_candidates_collapsed_by_canonical_id"] == 1


def test_propagation_diagnostics_deterministic() -> None:
    candidates = [
        {"candidate_asset_id": "a", "ticker": "AAPL", "exchange": "NASDAQ", "security_type": "equity"},
        {"candidate_asset_id": "b", "ticker": "MSFT", "exchange": "NASDAQ", "security_type": "equity"},
        {"candidate_asset_id": "c", "ticker": "", "exchange": "NASDAQ"},
    ]
    a = enrich_propagation_identities(candidates, REGISTRY)
    b = enrich_propagation_identities(candidates, REGISTRY)
    assert a == b
