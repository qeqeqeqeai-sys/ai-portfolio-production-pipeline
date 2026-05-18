import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.cross_registry_identity_governance import (
    build_cross_registry_governance,
    normalize_ticker_alias,
    run_cross_registry_identity_governance,
)


def test_exchange_qualified_alias_normalization_deterministic() -> None:
    assert normalize_ticker_alias(" brk.b ") == "BRK-B"
    assert normalize_ticker_alias("BRK/B") == "BRK-B"


def test_deterministic_alias_dual_listing_unresolved_and_conflict_governance() -> None:
    rows = [
        {"canonical_security_id": "sec1", "canonical_issuer_id": "iss1", "ticker": "BRK.B", "primary_exchange": "NYSE", "listing_exchange": "NYSE", "source_name": "primary"},
        {"canonical_security_id": "sec1", "canonical_issuer_id": "iss1", "ticker": "BRK/B", "primary_exchange": "NYSE", "listing_exchange": "NYSE", "source_name": "alias"},
        {"canonical_security_id": "sec2", "canonical_issuer_id": "iss2", "ticker": "RDS.A", "primary_exchange": "LSE", "listing_exchange": "NYSE", "source_name": "dual", "is_dual_listed": True},
        {"canonical_security_id": "sec3", "canonical_issuer_id": "iss3", "ticker": "ABC", "primary_exchange": "NYSE", "listing_exchange": "NYSE", "source_name": "conflict", "conflicting_alias": True},
        {"canonical_security_id": "", "canonical_issuer_id": "", "ticker": "ZZZ", "primary_exchange": "", "listing_exchange": "HKEX", "source_name": "unresolved"},
    ]
    out = build_cross_registry_governance(rows)
    counts = out["lineage_governance_status_counts"]
    assert counts["deterministic_alias"] >= 1
    assert counts["dual_listing_confirmed"] == 1
    assert counts["conflicting_cross_registry"] == 1
    assert counts["unresolved_cross_registry"] == 1
    assert out["linkage_mode"] == "deterministic_exact_match_only"
    assert out["enforcement_enabled"] is False
    assert out["canonical_override_enabled"] is False


def test_replay_hash_stability_and_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    rows = [
        {"canonical_security_id": "sec1", "canonical_issuer_id": "iss1", "ticker": "BRK.B", "primary_exchange": "NYSE", "listing_exchange": "NYSE", "source_name": "primary"},
        {"canonical_security_id": "sec1", "canonical_issuer_id": "iss1", "ticker": "BRK/B", "primary_exchange": "NYSE", "listing_exchange": "NYSE", "source_name": "alias"},
    ]
    a = run_cross_registry_identity_governance(rows)
    b = run_cross_registry_identity_governance(rows)
    assert a["replay"]["alias_structures_hash"] == b["replay"]["alias_structures_hash"]
    expected = [
        "logs/tier3h5_cross_registry_alias_summary.json",
        "logs/tier3h5_dual_listing_governance_summary.json",
        "logs/tier3h5_cross_registry_lineage_summary.json",
        "logs/tier3h5_alias_replay_governance_summary.json",
        "logs/tier3h5_phase3a_cross_registry_summary.json",
    ]
    for path in expected:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        assert payload["enforcement_enabled"] is False
        assert payload["canonical_override_enabled"] is False
