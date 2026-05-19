import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.canonical_registry_ingestion import run_registry_ingestion
from transmission_layers.asset_discovery.tier3h5.canonical_registry_sample_sources import SAMPLE_REGISTRY_SOURCES
from transmission_layers.asset_discovery.tier3h5.governance_contracts import (
    CANONICAL_OVERRIDE_ENABLED_DEFAULT,
    ENFORCEMENT_ENABLED_DEFAULT,
    REPLAY_SAFE_LINEAGE_ENABLED_DEFAULT,
    SUPPORTED_EXCHANGES,
    SUPPORTED_SECURITY_TYPES,
    classify_registry_candidate,
    governance_policy_summary,
    is_supported_exchange,
    is_supported_security_type,
)


def test_supported_exchange_recognition() -> None:
    assert is_supported_exchange("nyse")
    assert is_supported_exchange(" NASDAQ ")
    assert not is_supported_exchange("OTC")


def test_supported_security_type_recognition() -> None:
    assert is_supported_security_type("EQUITY")
    assert is_supported_security_type(" etf ")
    assert not is_supported_security_type("bond")


def test_unsupported_exchange_classification() -> None:
    classified = classify_registry_candidate("OTC", "equity")
    assert classified["exchange_supported"] is False
    assert classified["security_type_supported"] is True
    assert classified["is_supported_candidate"] is False


def test_unsupported_security_type_classification() -> None:
    classified = classify_registry_candidate("NYSE", "bond")
    assert classified["exchange_supported"] is True
    assert classified["security_type_supported"] is False
    assert classified["is_supported_candidate"] is False


def test_default_policy_remains_non_enforcing() -> None:
    summary = governance_policy_summary()
    assert summary["enforcement_enabled"] is ENFORCEMENT_ENABLED_DEFAULT is False
    assert summary["canonical_override_enabled"] is CANONICAL_OVERRIDE_ENABLED_DEFAULT is False
    assert summary["replay_safe_lineage_enabled"] is REPLAY_SAFE_LINEAGE_ENABLED_DEFAULT is True


def test_policy_summary_is_deterministic() -> None:
    assert governance_policy_summary() == governance_policy_summary()


def test_ingestion_uses_contract_supported_sets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_registry_ingestion("fixture_phase2a_global_coverage", SAMPLE_REGISTRY_SOURCES["fixture_phase2a_global_coverage"])
    summary = result["summary"]

    assert summary["records_seen"] == 10
    assert summary["records_accepted"] == 9
    assert summary["records_rejected"] == 1
    assert summary["unsupported_security_types"] == ["bond"]
    assert set(summary["exchange_coverage_breakdown"].keys()).issubset(SUPPORTED_EXCHANGES)
    assert set(summary["security_type_coverage_breakdown"].keys()).issubset(SUPPORTED_SECURITY_TYPES)


def test_no_behavior_drift_in_accept_reject_counts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_registry_ingestion("fixture_us_listings", SAMPLE_REGISTRY_SOURCES["fixture_us_listings"])
    summary = result["summary"]

    assert summary["records_seen"] == 4
    assert summary["records_accepted"] == 3
    assert summary["records_rejected"] == 0
    assert summary["duplicate_records_detected"] == 1
