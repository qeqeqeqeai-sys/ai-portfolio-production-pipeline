from transmission_layers.intelligence.tier5.federation_integrity import run_tier5h_federation_integrity
from transmission_layers.intelligence.tier5.federation_stabilization_report import build_federation_stabilization_report


def test_integrity_outputs_and_bounds_and_immutability():
    payloads = {
        "5a": {"federation_topology_score": 0.8, "tier5a_federation_checksum": "a"},
        "5b": {"federation_persistence_score": 0.7, "federation_persistence_checksum": "b"},
        "5c": {"federation_evolution_score": 0.6, "federation_evolution_checksum": "c"},
        "5d": {"federation_governance_score": 0.9, "federation_governance_checksum": "d"},
        "5e": {"federation_observability_score": 0.75, "federation_observability_checksum": "e"},
        "5f": {"federation_structural_health_score": 0.74, "federation_health_checksum": "f"},
        "5g": {"federation_resilience_score": 0.73, "federation_resilience_checksum": "g"},
    }
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
