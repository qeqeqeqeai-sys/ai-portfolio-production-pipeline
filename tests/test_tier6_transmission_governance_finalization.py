from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_propagation_distortion_diagnostics,
    assess_structural_signal_quality,
    assess_transmission_explainability,
    assess_transmission_governance_audit_trail,
    assess_transmission_governance_finalization,
    assess_transmission_governance_review_gate,
    assess_transmission_governance_summary,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
    assess_transmission_risk_register,
)

ALLOWED_LABELS = {
    "insufficient_structure", "api_contract_gap", "checksum_integrity_gap", "bounded_score_gap",
    "deterministic_contract_gap", "replay_safety_gap", "cross_tier_governance_gap",
    "governance_finalization_incomplete", "tier6_governance_finalized",
}


def _sample_topology():
    return {
        "nodes": [{"node_id": "a", "influence_score": 0.8}, {"node_id": "b", "influence_score": 0.7}, {"node_id": "c", "influence_score": 0.6}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.7},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.75},
        ],
    }


def test_deterministic_checksum_bounded_and_ordering_vocab_explanation():
    one = assess_transmission_governance_finalization(_sample_topology())
    two = assess_transmission_governance_finalization(_sample_topology())
    assert one == two
    assert one["checksum"] == two["checksum"]
    assert set(one["integration_labels"]).issubset(ALLOWED_LABELS)

    assert one["tier6_api_contracts"] == sorted(one["tier6_api_contracts"], key=lambda x: (-x["contract_score"], x["contract_id"]))
    assert one["checksum_integrity_validation"] == sorted(one["checksum_integrity_validation"], key=lambda x: (-x["validation_score"], x["validation_id"]))
    assert one["bounded_score_validation"] == sorted(one["bounded_score_validation"], key=lambda x: (-x["validation_score"], x["validation_id"]))
    assert one["deterministic_contract_validation"] == sorted(one["deterministic_contract_validation"], key=lambda x: (-x["validation_score"], x["validation_id"]))
    assert one["replay_safety_validation"] == sorted(one["replay_safety_validation"], key=lambda x: (-x["validation_score"], x["validation_id"]))
    assert one["cross_tier_governance_validation"] == sorted(one["cross_tier_governance_validation"], key=lambda x: (-x["validation_score"], x["validation_id"]))

    for score in [one["tier6_finalization_score"], *one["integration_components"].values()]:
        assert 0.0 <= score <= 1.0

    expected = (
        f"Transmission governance finalization completed: status={one['status']}; finalization={one['tier6_finalization_score']}; "
        f"primary_label={one['integration_labels'][0]}; api_contracts={len(one['tier6_api_contracts'])}; "
        f"replay_validations={len(one['replay_safety_validation'])}; cross_tier_validations={len(one['cross_tier_governance_validation'])}."
    )
    assert one["explanation"] == expected


def test_empty_missing_disconnected_and_gap_detection_and_immutability():
    assert assess_transmission_governance_finalization({})["status"] == "insufficient_structure"
    assert assess_transmission_governance_finalization({"nodes": []})["status"] == "insufficient_structure"
    assert assess_transmission_governance_finalization({"edges": []})["status"] == "insufficient_structure"
    weak = {"nodes": [{"node_id": "a", "influence_score": 0.0}], "edges": [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.0, "suppressed_for_propagation": True, "contradictory": True}]}
    out = assess_transmission_governance_finalization(weak)
    labels = set(out["integration_labels"])
    assert "api_contract_gap" in labels
    assert "checksum_integrity_gap" not in labels
    assert "bounded_score_gap" not in labels
    assert "deterministic_contract_gap" in labels or "replay_safety_gap" in labels
    assert "cross_tier_governance_gap" in labels or "replay_safety_gap" in labels
    assert "governance_finalization_incomplete" in labels

    topo = _sample_topology()
    original = deepcopy(topo)
    _ = assess_transmission_governance_finalization(topo)
    assert topo == original


def test_public_export_and_tier_non_regression_smoke():
    from transmission_layers.intelligence.tier6 import assess_transmission_governance_finalization as exported
    assert exported is assess_transmission_governance_finalization

    topology = _sample_topology()
    assert "signal_quality_score" in assess_structural_signal_quality(topology)
    assert "transmission_reliability_score" in assess_transmission_reliability_diagnostics(topology)
    assert "path_integrity_score" in assess_transmission_path_integrity(topology)
    assert "propagation_integrity_score" in assess_propagation_distortion_diagnostics(topology)
    assert "explainability_score" in assess_transmission_explainability(topology)
    assert "risk_register_score" in assess_transmission_risk_register(topology)
    assert "governance_score" in assess_transmission_governance_summary(topology)
    assert "governance_certification_score" in assess_transmission_governance_review_gate(topology)
    assert "audit_integrity_score" in assess_transmission_governance_audit_trail(topology)
    assert "simulation_health_state" in run_structural_simulation(topology)
