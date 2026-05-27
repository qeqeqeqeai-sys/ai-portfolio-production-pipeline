from transmission_layers.expectation_failure.obs300_4b_ecosystem_state_compression_structural_signal_prioritization import (
    build_obs300_4b_ecosystem_state_compression_structural_signal_prioritization,
)


def _payload() -> dict[str, object]:
    return {
        "dominant_stress_signal": 76,
        "topology_pressure_signal": 71,
        "dominant_recovery_signal": 60,
        "normalization_pathway_signal": 64,
        "dominant_transition_signal": 68,
        "transition_bridge_signal": 70,
        "dominant_fragmentation_signal": 62,
        "semantic_congestion_signal": 57,
        "dominant_resilience_signal": 66,
        "continuity_domain_signal": 69,
        "stress_relevance": 78,
        "stress_persistence": 74,
        "stress_propagation": 80,
        "stress_bridge_significance": 67,
        "stress_impact": 82,
        "recovery_relevance": 64,
        "recovery_persistence": 62,
        "recovery_propagation": 61,
        "recovery_bridge_significance": 58,
        "recovery_impact": 63,
        "transition_relevance": 70,
        "transition_persistence": 66,
        "transition_propagation": 68,
        "transition_bridge_significance": 79,
        "transition_impact": 72,
        "resilience_relevance": 67,
        "resilience_persistence": 71,
        "resilience_propagation": 65,
        "resilience_bridge_significance": 62,
        "resilience_impact": 69,
        "fragmentation_relevance": 59,
        "fragmentation_persistence": 63,
        "fragmentation_propagation": 58,
        "fragmentation_bridge_significance": 55,
        "fragmentation_impact": 61,
        "topology_saturation_signal": 60,
        "repetitive_signal_density": 52,
        "redundant_pathway_density": 49,
        "monoculture_signal_density": 47,
    }


def test_obs300_4b_deterministic_outputs_and_required_surfaces():
    first = build_obs300_4b_ecosystem_state_compression_structural_signal_prioritization(_payload())
    second = build_obs300_4b_ecosystem_state_compression_structural_signal_prioritization(_payload())

    assert first == second
    assert first["module"] == "OBS300-4B"
    assert "ecosystem_state_compression_summary" in first
    assert "structural_signal_prioritization" in first
    assert "ecosystem_attention_allocation" in first
    assert "noise_suppression_layer" in first
    assert "ecosystem_posture_classification" in first
    assert "operator_facing_visualization_payloads" in first


def test_obs300_4b_bounded_payload_sizes_and_prioritization_stability():
    result = build_obs300_4b_ecosystem_state_compression_structural_signal_prioritization(_payload())

    ranked = result["structural_signal_prioritization"]["ranked_structural_signals"]
    assert len(ranked) == 5
    assert ranked == sorted(ranked, key=lambda r: (-r["structural_priority_score"], r["signal"]))

    for row in ranked:
        assert 0 <= row["structural_priority_score"] <= 100
        assert 0 <= row["relevance_score"] <= 100
        assert 0 <= row["persistence_weight"] <= 100

    summary = result["ecosystem_state_compression_summary"]
    assert len(summary["dominant_stress_structure"]) <= 280
    assert len(summary["ecosystem_posture_summary"]) <= 280

    attention = result["ecosystem_attention_allocation"]
    assert len(attention["highest_priority_ecosystem_signals"]) <= 6


def test_obs300_4b_governance_boundary_and_non_autonomous_constraints():
    result = build_obs300_4b_ecosystem_state_compression_structural_signal_prioritization(_payload())

    assert result["governance_certification"] == {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    architecture = result["signal_prioritization_architecture_summary"]
    assert architecture["graph_execution_engine_required"] is False
    assert architecture["topology_activation_required"] is False
    assert architecture["autonomous_replay_required"] is False
    assert architecture["sql_write_required"] is False

    operational = result["operational_report"]
    assert operational["autonomous_logic"] is False
    assert operational["sql_writes_enabled"] is False
    assert operational["prediction_or_trading_execution"] is False


def test_obs300_4b_posture_and_noise_suppression_stability():
    result = build_obs300_4b_ecosystem_state_compression_structural_signal_prioritization(_payload())

    posture = result["ecosystem_posture_classification"]["posture"]
    assert posture in {
        "fragmented",
        "stabilizing",
        "transitioning",
        "resilient",
        "stress_dominant",
        "normalization_dominant",
        "mixed_transition",
        "decompression_emerging",
    }

    for v in result["noise_suppression_layer"].values():
        assert 0 <= v <= 100
