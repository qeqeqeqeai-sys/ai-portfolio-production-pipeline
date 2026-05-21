from transmission_layers.intelligence.tier5 import federation_integrity as fi
from transmission_layers.intelligence.tier5.federation_integrity import run_tier5h_federation_integrity
from transmission_layers.intelligence.tier5.federation_stabilization_report import build_federation_stabilization_report


def _base_payloads() -> dict[str, dict[str, float | str]]:
    return {
        "5a": {"federation_topology_score": 0.8, "tier5a_federation_checksum": "a"},
        "5b": {"federation_persistence_score": 0.7, "federation_persistence_checksum": "b"},
        "5c": {"federation_evolution_score": 0.6, "federation_evolution_checksum": "c"},
        "5d": {"federation_governance_score": 0.9, "federation_governance_checksum": "d"},
        "5e": {"federation_observability_score": 0.75, "federation_observability_checksum": "e"},
        "5f": {"federation_structural_health_score": 0.74, "federation_health_checksum": "f"},
        "5g": {"federation_resilience_score": 0.73, "federation_resilience_checksum": "g"},
    }


def test_integrity_outputs_and_bounds_and_immutability():
    payloads = _base_payloads()
    snapshot = {k: dict(v) for k, v in payloads.items()}
    out = run_tier5h_federation_integrity(federation_id="fed-1", tier_payloads=payloads)
    assert payloads == snapshot
    for key in [
        "federation_integrity_score",
        "bounded_federation_integrity_score",
        "federation_determinism_score",
        "federation_score_contract_score",
        "federation_checksum_contract_score",
        "federation_replay_contract_score",
        "federation_export_contract_score",
        "federation_immutability_contract_score",
        "federation_stabilization_gap_score",
    ]:
        assert 0.0 <= out[key] <= 1.0
    rep = build_federation_stabilization_report(out)
    assert "federation_stabilization_report_checksum" in rep


def test_classification_precedence_score_over_all(monkeypatch):
    monkeypatch.setattr(fi, "validate_score_contracts", lambda payload: {
        "score_keys": ["a_score"], "bounded_score_keys": [], "federation_score_contract_score": 0.0,
        "federation_checksum_contract_score": 0.0, "federation_score_contracts_checksum": "x"
    })
    monkeypatch.setattr(fi, "validate_replay_contract", lambda payload: {
        "federation_replay_contract_score": 0.0, "federation_determinism_score": 0.0,
        "federation_determinism_checksum": "d", "federation_replay_contracts_checksum": "r"
    })
    monkeypatch.setattr(fi, "collect_tier5_export_inventory", lambda: {
        "tier5_public_exports": [], "tier5_ranking_helpers": [], "federation_export_contract_score": 0.0, "federation_export_contracts_checksum": "e"
    })
    out = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=_base_payloads())
    assert out["federation_integrity_classification"] == "score_contract_gap"


def test_classification_precedence_checksum_over_lower_gaps(monkeypatch):
    monkeypatch.setattr(fi, "validate_score_contracts", lambda payload: {
        "score_keys": ["a_score"], "bounded_score_keys": ["a_score"], "federation_score_contract_score": 1.0,
        "federation_checksum_contract_score": 0.0, "federation_score_contracts_checksum": "x"
    })
    monkeypatch.setattr(fi, "validate_replay_contract", lambda payload: {
        "federation_replay_contract_score": 0.0, "federation_determinism_score": 0.0,
        "federation_determinism_checksum": "d", "federation_replay_contracts_checksum": "r"
    })
    monkeypatch.setattr(fi, "collect_tier5_export_inventory", lambda: {
        "tier5_public_exports": [], "tier5_ranking_helpers": [], "federation_export_contract_score": 0.0, "federation_export_contracts_checksum": "e"
    })
    out = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=_base_payloads())
    assert out["federation_integrity_classification"] == "checksum_contract_gap"


def test_classification_precedence_replay_over_export_immutability_fragmentation_and_stabilization(monkeypatch):
    monkeypatch.setattr(fi, "validate_score_contracts", lambda payload: {
        "score_keys": ["a_score"], "bounded_score_keys": ["a_score"], "federation_score_contract_score": 1.0,
        "federation_checksum_contract_score": 1.0, "federation_score_contracts_checksum": "x"
    })
    monkeypatch.setattr(fi, "validate_replay_contract", lambda payload: {
        "federation_replay_contract_score": 0.0, "federation_determinism_score": 0.0,
        "federation_determinism_checksum": "d", "federation_replay_contracts_checksum": "r"
    })
    monkeypatch.setattr(fi, "collect_tier5_export_inventory", lambda: {
        "tier5_public_exports": [], "tier5_ranking_helpers": [], "federation_export_contract_score": 0.0, "federation_export_contracts_checksum": "e"
    })
    out = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=_base_payloads())
    assert out["federation_integrity_classification"] == "replay_contract_gap"


def test_classification_precedence_export_over_immutability_fragmentation_and_stabilization(monkeypatch):
    monkeypatch.setattr(fi, "validate_score_contracts", lambda payload: {
        "score_keys": ["a_score"], "bounded_score_keys": ["a_score"], "federation_score_contract_score": 1.0,
        "federation_checksum_contract_score": 1.0, "federation_score_contracts_checksum": "x"
    })
    monkeypatch.setattr(fi, "validate_replay_contract", lambda payload: {
        "federation_replay_contract_score": 1.0, "federation_determinism_score": 1.0,
        "federation_determinism_checksum": "d", "federation_replay_contracts_checksum": "r"
    })
    monkeypatch.setattr(fi, "collect_tier5_export_inventory", lambda: {
        "tier5_public_exports": [], "tier5_ranking_helpers": [], "federation_export_contract_score": 0.0, "federation_export_contracts_checksum": "e"
    })
    out = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=_base_payloads())
    assert out["federation_integrity_classification"] == "export_contract_gap"


def test_classification_precedence_immutability_over_fragmentation_and_stabilization(monkeypatch):
    monkeypatch.setattr(fi, "validate_score_contracts", lambda payload: {
        "score_keys": ["a_score"], "bounded_score_keys": ["a_score"], "federation_score_contract_score": 1.0,
        "federation_checksum_contract_score": 1.0, "federation_score_contracts_checksum": "x"
    })
    monkeypatch.setattr(fi, "validate_replay_contract", lambda payload: {
        "federation_replay_contract_score": 1.0, "federation_determinism_score": 1.0,
        "federation_determinism_checksum": "d", "federation_replay_contracts_checksum": "r"
    })
    monkeypatch.setattr(fi, "collect_tier5_export_inventory", lambda: {
        "tier5_public_exports": ["build_federation_stabilization_report", "build_x_sort_key"], "tier5_ranking_helpers": ["build_x_sort_key"], "federation_export_contract_score": 1.0, "federation_export_contracts_checksum": "e"
    })
    monkeypatch.setattr(fi, "deepcopy", lambda x: {})
    out = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=_base_payloads())
    assert out["federation_integrity_classification"] == "immutability_contract_gap"


def test_deterministic_but_fragmented_reachable(monkeypatch):
    monkeypatch.setattr(fi, "collect_tier5_export_inventory", lambda: {
        "tier5_public_exports": ["build_x_sort_key", "build_federation_stabilization_report"], "tier5_ranking_helpers": ["build_x_sort_key"], "federation_export_contract_score": 1.0, "federation_export_contracts_checksum": "e"
    })
    monkeypatch.setattr(fi, "mean_bounded", lambda _: 0.9)
    payloads = _base_payloads()
    payloads.pop("5g")
    out = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=payloads)
    assert out["federation_integrity_classification"] == "deterministic_but_fragmented"


def test_stable_reachable_when_all_contract_areas_healthy(monkeypatch):
    monkeypatch.setattr(fi, "collect_tier5_export_inventory", lambda: {
        "tier5_public_exports": ["build_x_sort_key", "build_federation_stabilization_report"], "tier5_ranking_helpers": ["build_x_sort_key"], "federation_export_contract_score": 1.0, "federation_export_contracts_checksum": "e"
    })
    out = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=_base_payloads())
    assert out["federation_integrity_classification"] == "stable"


def test_repeated_calls_identical_classification_and_checksum():
    payloads = _base_payloads()
    one = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=payloads)
    two = run_tier5h_federation_integrity(federation_id="fed", tier_payloads=payloads)
    assert one["federation_integrity_classification"] == two["federation_integrity_classification"]
    assert one["federation_integrity_checksum"] == two["federation_integrity_checksum"]
