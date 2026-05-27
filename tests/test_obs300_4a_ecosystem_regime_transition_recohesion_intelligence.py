from transmission_layers.expectation_failure.obs300_4a_ecosystem_regime_transition_recohesion_intelligence import (
    build_obs300_4a_ecosystem_regime_transition_recohesion_intelligence,
)


def _payload() -> dict[str, object]:
    return {
        "tightening_stabilization_signal": 72,
        "disinflation_normalization_signal": 68,
        "capex_margin_normalization_signal": 63,
        "fragmentation_recohesion_signal": 74,
        "structural_transition_signal": 70,
        "cross_regime_topology_signal": 66,
        "transition_continuity_signal": 71,
        "transition_dislocation_signal": 24,
        "normalization_migration_signal": 69,
        "normalization_transmission_signal": 65,
        "narrative_recohesion_signal": 75,
        "decomposition_reconnection_signal": 70,
        "topology_realignment_signal": 73,
        "synchronization_recovery_signal": 72,
        "synchronization_dispersion_signal": 25,
        "cross_regime_bridge_signal": 74,
        "stabilization_bridge_persistence_signal": 70,
        "transition_bridge_continuity_signal": 71,
        "strongest_transition_bridges": ["a->b", "c->d"],
        "highest_recohesion_clusters": ["cluster_a", "cluster_b"],
        "normalization_migration_observations": ["n1", "n2"],
        "cross_regime_propagation_pathways": ["p1", "p2"],
    }


def test_obs300_4a_deterministic_outputs_and_required_surfaces():
    first = build_obs300_4a_ecosystem_regime_transition_recohesion_intelligence(_payload())
    second = build_obs300_4a_ecosystem_regime_transition_recohesion_intelligence(_payload())

    assert first == second
    assert first["module"] == "OBS300-4A"
    assert "ecosystem_regime_transition_observation" in first
    assert "narrative_recohesion_observation" in first
    assert "cross_regime_bridge_intelligence" in first
    assert "ecosystem_transition_intelligence_summary" in first
    assert "operator_facing_visualization_payloads" in first
    assert "governance_certification" in first


def test_obs300_4a_bounded_payload_sizes_and_scoring_stability():
    result = build_obs300_4a_ecosystem_regime_transition_recohesion_intelligence(_payload())

    transition = result["ecosystem_regime_transition_observation"]
    recohesion = result["narrative_recohesion_observation"]
    bridge = result["cross_regime_bridge_intelligence"]

    assert 0 <= transition["regime_transition_score"] <= 100
    assert 0 <= transition["structural_transition_observation_score"] <= 100
    assert 0 <= transition["transition_continuity_score"] <= 100
    assert 0 <= recohesion["narrative_recohesion_score"] <= 100
    assert 0 <= recohesion["synchronization_recovery_score"] <= 100
    assert 0 <= bridge["cross_regime_bridge_score"] <= 100

    assert len(transition["cross_regime_propagation_pathways"]) <= 8
    assert len(result["ecosystem_transition_intelligence_summary"]["strongest_transition_bridges"]) <= 8
    assert len(result["ecosystem_transition_intelligence_summary"]["highest_recohesion_clusters"]) <= 8

    assert len(recohesion["decomposed_pathway_reconnection_observation"]) <= 260
    assert len(result["ecosystem_transition_intelligence_summary"]["ecosystem_transition_topology_summaries"]) <= 260


def test_obs300_4a_governance_boundaries_and_no_execution_paths():
    result = build_obs300_4a_ecosystem_regime_transition_recohesion_intelligence(_payload())
    governance = result["governance_certification"]

    assert governance == {
        "observational_only": True,
        "no_recursive_replay_operationalization": True,
        "no_autonomous_replay": True,
        "no_topology_activation": True,
        "no_self_modifying_pathways": True,
        "no_prediction_or_trading_execution": True,
        "no_sql_write_introduction": True,
    }

    architecture = result["regime_transition_architecture_summary"]
    assert architecture["graph_execution_engine_required"] is False
    assert architecture["topology_activation_required"] is False
    assert architecture["autonomous_replay_required"] is False

    operational = result["operational_report"]
    assert operational["autonomous_logic"] is False
    assert operational["sql_writes_enabled"] is False
    assert operational["prediction_or_trading_execution"] is False
